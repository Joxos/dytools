# Draft: Douyu Danmu Modular Refactoring Plan

## Requirements (confirmed)
- Priority 1: Add message buffering - fix UTF-8 truncation data loss
- Priority 2: Implement async version - handle high-pressure scenarios
- Priority 3: Improve type definitions - DanmuMessage dataclass
- Priority 4: Add abstraction layer - custom storage handler

## Technical Decisions
- Use `websockets` library for async version (not aiohttp, more appropriate for WS)
- Abstract base class `StorageHandler` with `save(message)` and `close()` methods
- Default implementations: `CSVStorage`, `ConsoleStorage`
- Keep backward compatible: existing CLI works as before
- Use uv for dependency management (as per .ai/HOW_TO.md)

## Research Findings
- UTF-8 truncation happens when server splits multi-byte chars across packets
- Solution: buffer accumulates bytes until complete packet received
- Packet format: 4-byte length at offset 0, total_length = length + 4

## Open Questions
- Should we keep the old single-file approach or create a package?
- Package approach: douyu_danmu/ with __init__.py, protocol.py, storage.py, collectors.py

## Scope Boundaries
- IN: Refactor to modular structure, add async, fix UTF-8, abstract storage
- OUT: Database storage,统计分析 (user said "回头再做")
- Keep simple CLI interface unchanged

## Git Commit Strategy
Each commit should be atomic and testable:
1. refactor: extract protocol to separate module
2. feat: add DanmuMessage dataclass and types
3. feat: add message buffer to fix UTF-8
4. feat: add abstract storage layer
5. feat: add async collector with websockets
6. chore: update CLI to support new features

## Python Tools (from .ai/HOW_TO.md)
- ruff format
- ruff check
- pyright
- uv for package management
