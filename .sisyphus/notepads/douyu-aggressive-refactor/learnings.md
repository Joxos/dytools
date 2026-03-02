# Learnings - Douyu Aggressive Refactoring

This file captures conventions, patterns, and best practices discovered during the aggressive refactoring process.

---

## Inherited Wisdom from Previous Refactor

### Project Constraints (From .ai/HOW_TO.md)
- Use `uv` for ALL dependency management, NEVER touch global pip
- Use PEP 585 built-in type hints (no typing module imports)
- Google Style docstrings for all classes and functions
- Code comments ALWAYS in English
- No backward compatibility concerns - aggressive refactoring allowed
- Use loguru instead of built-in logging
- No tests unless user requests them

### Previous Refactor Achievements (v2.0.0)
- Successfully modularized from single file to 7-module package
- MessageBuffer eliminates UTF-8 truncation bugs
- StorageHandler abstraction enables pluggable backends
- Both SyncCollector and AsyncCollector verified working
- All quality gates passed: ruff format, ruff check, pyright
- Runtime verified with real Douyu WebSocket connections

### Key Technical Patterns
- **UTF-8 Safety**: MessageBuffer accumulates raw bytes until complete packet boundary
- **SSL Configuration**: Douyu requires `set_ciphers("DEFAULT@SECLEVEL=1")` for both sync/async
- **Storage Pattern**: Context manager protocol ensures cleanup even on exceptions
- **Heartbeat**: 45-second interval, daemon thread (sync) or asyncio.Task (async)
- **Protocol**: 4-byte little-endian packet length + 8-byte header + body + null terminator

### PostgreSQL Config (User Confirmed)
- Host: localhost
- Port: 5432
- Database: douyu_danmu
- User: douyu
- Password: douyu6657

---


## T1: Setup Loguru Logging Configuration

### Completed Actions
1. **Added Dependencies**:
   - Added `loguru>=0.7.0` and `psycopg2-binary>=2.9.0` to both `requirements.txt` and `pyproject.toml`
   - Used `uv` for dependency management

2. **Created Log Module** (`douyu_danmu/log.py`):
   - Pre-configured logger instance using loguru
   - Removed default handler to prevent duplicate logging
   - Added colored stderr handler with ISO 8601 timestamps
   - Format: `<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>`
   - Default log level set to INFO (aligns with user requirement for async/thread-safe logging)

3. **Replaced All Logging Imports**:
   - **douyu_danmu/__main__.py**: 
     - Removed `import logging` 
     - Removed `_setup_logging()` function (replaced with pre-configured loguru)
     - Replaced all `logging.*` calls with direct `logger.*` calls
   - **douyu_danmu/collectors.py**:
     - Removed `import logging`
     - Replaced all 30+ logging statements with `logger.*` calls (affects both SyncCollector and AsyncCollector)
   - **douyu_danmu/buffer.py**:
     - Removed `import logging`
     - Replaced all 3 warning/error calls with `logger.*` calls
   - **douyu_danmu/protocol.py**:
     - Removed `import logging`
     - Replaced 1 warning call with `logger.warning()`

4. **Verification**:
   - ✅ No remaining `import logging` or `from logging import` statements in codebase
   - ✅ All Python files compile without syntax errors
   - ✅ Logger import works: `from douyu_danmu.log import logger`
   - ✅ CLI help works: `python -m douyu_danmu --help`
   - ✅ All module imports successful: SyncCollector, AsyncCollector, CSVStorage, ConsoleStorage

### Key Design Decisions
1. **Logger Export Pattern**: Export `logger = _logger` from log.py for clean import syntax
2. **Pre-configured vs Runtime Configuration**: Chose pre-configured at module load to support both CLI and API usage
3. **No Dependency on argparse**: Logger initialization doesn't depend on CLI args (unlike previous logging.basicConfig)
4. **Loguru Benefits Achieved**:
   - ✅ Thread-safe logging (satisfies SyncCollector heartbeat thread requirement)
   - ✅ Async-safe logging (satisfies AsyncCollector asyncio requirement)
   - ✅ Colored output by default
   - ✅ ISO 8601 timestamps
   - ✅ Function/module context in output

### Testing Notes
- Logger tested with both `logger.info()` and `logger.error()` calls
- Colored output verified in terminal (ANSI codes working)
- Zero import conflicts with loguru

### User Requirement Satisfaction
- ✅ "不要使用内置logging，使用支持异步和线程安全的loguru" - SATISFIED
  - Removed all built-in logging usage
  - loguru is async-safe and thread-safe
  - Both SyncCollector and AsyncCollector can now log from concurrent execution contexts without issues


## T4: Storage Package Refactoring Complete

### Key Learnings

1. **Package Structure**: Successfully created `douyu_danmu/storage/` as a proper Python package with:
   - `storage/base.py`: Contains only StorageHandler ABC (160 lines)
   - `storage/__init__.py`: Contains both base class import + concrete implementations (CSVStorage, ConsoleStorage)

2. **Circular Import Avoidance**: Kept CSVStorage and ConsoleStorage implementations in `storage/__init__.py` during Wave 1 (temporary arrangement). This avoids the circular import that would occur if we tried to import from `../storage.py` when the module IS `storage/`.

3. **Import Strategy**: 
   - Public API remains unchanged: `from douyu_danmu.storage import StorageHandler, CSVStorage, ConsoleStorage`
   - Internal: `from .base import StorageHandler` + concrete implementations in `__init__.py`
   - This allows Wave 2 to split implementations into separate files (csv.py, console.py) with minimal changes

4. **Type Safety**: 
   - No new type errors introduced
   - All existing pyright errors are in collectors.py and protocol.py (pre-existing)
   - Storage package passes type checking cleanly

5. **Backward Compatibility**:
   - All existing imports still work
   - CLI still works: `python -m douyu_danmu --help`
   - No changes needed to collectors.py or other modules

### Wave 2 Preparation

The current structure makes Wave 2 straightforward:
1. Move CSVStorage from `storage/__init__.py` → `storage/csv.py`
2. Move ConsoleStorage from `storage/__init__.py` → `storage/console.py`
3. Add PostgreSQL implementation in `storage/postgres.py`
4. Update `storage/__init__.py` to import all three modules
5. Delete original `douyu_danmu/storage.py` file (now `storage/` is the module)

### Commit Checklist
- [x] Directory created: `douyu_danmu/storage/`
- [x] Files created: `storage/__init__.py` and `storage/base.py`
- [x] Imports updated: `douyu_danmu/__init__.py` already uses correct imports
- [x] All imports verified: `pyright` and manual tests pass
- [x] CLI works: `python -m douyu_danmu --help` works
- [x] Backward compatibility maintained


## T5: Collectors Package Refactoring - Extract SyncCollector

### Completed Actions

1. **Created `douyu_danmu/collectors/` Package Structure**:
   - Created directory: `douyu_danmu/collectors/`
   - Created `collectors/sync.py`: SyncCollector class extracted from old collectors.py
   - Created `collectors/async_.py`: AsyncCollector class extracted (ahead of T6)
   - Created `collectors/__init__.py`: Proper exports

2. **SyncCollector Extraction** (`collectors/sync.py`):
   - Moved SyncCollector class from collectors.py → sync.py
   - Updated all relative imports:
     - `from ..buffer import MessageBuffer`
     - `from ..log import logger`
     - `from ..protocol import DOUYU_WS_URL, encode_message, serialize_message`
     - `from ..storage import StorageHandler`
     - `from ..types import DanmuMessage, MessageType`
   - Removed unused `Any` import to satisfy pyright
   - Preserved all docstrings (module and class)
   - Preserved all methods: `__init__`, `connect`, `stop`, `_on_message`, `_on_error`, `_on_close`, `_on_open`, `_heartbeat_loop`

3. **AsyncCollector Pre-extraction** (`collectors/async_.py`):
   - Extracted AsyncCollector to async_.py AHEAD of T6 schedule
   - Rationale: Avoids circular import issues that arise when package shadows old module
   - When `collectors/` package exists, Python treats `..collectors` as the package, not the old file
   - This prevents the need for importlib workarounds
   - T6 will now only need to delete the old collectors.py file

4. **Package Initialization** (`collectors/__init__.py`):
   - Exports both SyncCollector and AsyncCollector
   - Public API remains unchanged: `from douyu_danmu.collectors import SyncCollector, AsyncCollector`
   - Backwards compatible with existing code

5. **Verification**:
   - ✅ Direct imports work: `from douyu_danmu.collectors import SyncCollector, AsyncCollector`
   - ✅ CLI works: `python -m douyu_danmu --help` produces expected output
   - ✅ pyright error count unchanged (19 errors, same pre-existing ones)
   - ✅ Removed unused imports (Any) to keep code clean

### Key Technical Decisions

1. **AsyncCollector Extraction (Ahead of Schedule)**:
   - Original plan was to leave AsyncCollector in old collectors.py until T6
   - When creating a `collectors/` package, the old `collectors.py` file becomes unreachable
   - Python's module resolution prefers packages over files
   - Solution: Extract AsyncCollector to `async_.py` now (T6 work done early)
   - Avoids circular import workarounds and importlib hacks
   - Cleaner approach that maintains package structure integrity

2. **Module Naming: `async_.py` not `async.py`**:
   - Cannot use `async` as module name (reserved keyword)
   - Using `async_` suffix is Python convention for reserved keywords
   - Import is `from .async_ import AsyncCollector` - clean and idiomatic

3. **Relative Imports**:
   - Using `..` to access parent package modules
   - Consistent with storage/ package pattern from T4
   - Allows collectors to be moved/reorganized without breaking internal references

### Comparison with T4 (Storage Package)

| Aspect | Storage Package (T4) | Collectors Package (T5) |
|--------|---------------------|------------------------|
| Original Structure | Single storage.py file | Single collectors.py file |
| New Structure | storage/__init__.py + storage/base.py | collectors/__init__.py + sync.py + async_.py |
| Implementation Split | Delayed to Wave 2 (concrete impls in __init__.py) | Done in T5 (both in separate files) |
| Circular Import Handling | N/A (implementations stayed in __init__.py) | Avoided by extracting async.py early |
| Public API | Unchanged | Unchanged |

### Files Created/Modified

- ✅ Created: `douyu_danmu/collectors/__init__.py` (38 lines)
- ✅ Created: `douyu_danmu/collectors/sync.py` (249 lines)
- ✅ Created: `douyu_danmu/collectors/async_.py` (310 lines)
- ⚠️  Kept (not deleted): `douyu_danmu/collectors.py` (original, will be deleted in T6)
- ✅ Other files: No changes needed (imports resolved automatically)

### T6 Preparation

After T5, T6 only needs to:
1. Delete `douyu_danmu/collectors.py` (old file is now obsolete)
2. No import changes needed anywhere
3. All internal references already point to collectors/ package

### Error Count Tracking

- Before T5: 19 pyright errors (pre-existing in collectors.py)
- After T5: 19 pyright errors (same errors now in collectors/sync.py and collectors/async_.py)
- No new errors introduced ✅
- Errors are all in WebSocket library type stubs (reportUnknownMemberType)

