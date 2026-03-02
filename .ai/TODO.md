# TODO

## Completed

### ~~MRO-aware affair type resolution in `exec_order()`~~ — DONE

Implemented via `MutableAffair.emit_up` field (`bool`, default `False`).
When `True`, `BaseDispatcher._resolve_affair_types()` walks the affair's MRO
(child-first) and `emit()` fires callbacks registered on each ancestor type.
Cross-hierarchy key conflicts raise `KeyConflictError` (expected fail-fast).

Affected files: `affairs.py`, `base_dispatcher.py`, `dispatcher.py`,
`async_dispatcher.py`. Tests in `test_dispatcher.py::TestEmitUp` and
`test_async_dispatcher.py::TestAsyncEmitUp`.

### ~~Full logging support~~ — DONE

Added `loguru` DEBUG-level logging to core modules: `registry.py` (add/remove),
`dispatcher.py` and `async_dispatcher.py` (emit), `aware.py` (method binding).
All affairon logging disabled by default via `logger.disable("affairon")` in
`__init__.py`; users opt in with `logger.enable("affairon")`.

Affected files: `__init__.py`, `registry.py`, `dispatcher.py`,
`async_dispatcher.py`, `aware.py`, `pyproject.toml` (E402 per-file-ignore).
README updated with "Logging" section. AGENTS.md updated with conventions.

### ~~Callback result type enforcement~~ — DONE

Added `isinstance(result, dict)` check in both `dispatcher.py` and
`async_dispatcher.py`. Returns non-dict/non-None raise `TypeError` with
callback name via `callable_name()`.

---

## Phase 1: Core Framework Completion

### ~~P1 — Affair filtering~~ — DONE

Added `when` predicate parameter to `on()` and `on_method()`. Callbacks
only fire when `when(affair)` returns `True`. Prevents meta-affair
recursion in P2.

Commit: `2176c6e`.

### ~~P2 — CallbackErrorAffair~~ — DONE

Emit `CallbackErrorAffair` when a callback raises, with retry,
deadletter, and silent policies. Uses P1 filtering to prevent
recursion. Meta-depth guard (≤1) as fail-fast.

Commit: `15e0fb2`.

### ~~P3 — Key conflict resolution strategies~~ — DONE

Added configurable merge strategies: fail-fast (default),
last-write-wins, list-append, and custom resolver via constructor
parameter. Also supports affair-level `merge_strategy` override.

Commit: `107c3fd`.

### P4 — Type annotation consistency

Audit and ensure type annotations are consistent across the codebase:
callback type signatures, return types, generic bounds, etc.
---

## Phase 2: Power Features

### P5 — Middleware / interceptor chain

Framework-level hooks that wrap `emit()` execution for cross-cutting
concerns (timing, auth, error policy, dry-run, rate limiting).
Implementation shape: `(affair, call_next) -> result` chain.

### P6 — Configurable execution ordering strategy

Make the callback execution ordering strategy pluggable via constructor
parameter or strategy object. Currently hardcoded to BFS layering
(`nx.bfs_layers`). Users may need topological sort, custom priority,
or weighted ordering for specific use cases.

```python
BaseRegistry(layerer="bfs"|"topological"|custom_callable)
```

### P7 — Affair tracing

#### Emit flow diagram generation from code

Static analysis or runtime introspection to generate a visual graph of
which affairs trigger which callbacks, including dependency ordering and
emit_up propagation paths.

#### Continuous emit tracing in dispatcher

Runtime tracing that records the full chain of affair emissions,
including nested/recursive emits, with timing and result data.
Useful for debugging complex affair cascades.

### P8 — Simple configuration layer for error handling

Provide simple enum/field-based configuration for common error handling
strategies (e.g., `on_error="raise"|"skip"|"log"`, `retry_limit`,
`retry_backoff`) so most users don't need to touch MetaAffair callbacks.
Deferred: actual usage patterns may diverge significantly depending on
the application domain; design after MetaAffair error handling is proven.

---

## Phase 3: Ecosystem

### P9 — Publish to PyPI

Set up GitHub Actions workflow with Trusted Publishers (OIDC) for
automated publishing on release tag creation. Use `pypa/gh-action-pypi-publish`.
Test on TestPyPI first.

### P10 — Plugin load error as MetaAffair

Emit a `PluginLoadErrorAffair` meta-affair when plugin loading fails,
allowing users to selectively skip, substitute, or abort plugins.
Currently all plugin errors are hard `raise`. This is a real but
uncommon scenario; implement after core MetaAffair patterns are stable.

### P11 — Affair schema version control

Define a strategy for evolving affair field schemas across plugin
ecosystem versions: field addition, removal, rename, type change.
How do old callbacks handle new fields? How do new callbacks degrade
on old affair versions?

---

## Phase 4: Advanced

### P12 — Distributed emit

Extend `emit()` beyond in-process to support cross-process and
cross-machine affair dispatch via message queues (e.g., Redis,
RabbitMQ, NATS). Requires serialization strategy for affairs
and result aggregation across network boundaries.

### P13 — Dead letter queue

Emit `AffairDeadLetteredAffair` when an affair has no registered
listeners or all listeners fail. Provides observability and recovery
for lost affairs. Placed after distributed emit because dead letter
is inherently a queue concept.

### P14 — IDE plugin for affairon

Developer tooling: affair seam visualization, callback dependency
graph viewer, go-to-definition for affair-to-callback relationships,
autocomplete for `after` parameters. Target VS Code first.

---

## Project Practice (Real-World Validation)

### PP1 — pluggy migration guide

Write a guide for migrating from pluggy to affairon: concept mapping
(hookspec -> affair, hookimpl -> callback), API equivalences, and
migration steps.

### PP2 — Reimplement pluggy official examples with affairon

Port pluggy's official documentation examples to affairon to
demonstrate equivalent (or superior) expressiveness.

### PP3 — Replace pluggy as pytest's plugin backend

Investigate feasibility of affairon as a drop-in replacement for
pluggy in pytest. Identify API gaps, compatibility requirements,
and required adapter layers.

### PP4 — Benchmark: affairon-backed pytest vs original

After prototype replacement, measure performance delta: test
discovery time, hook call overhead, memory usage, and overall
test suite execution time.

### PP5 — Build an affair-driven web application framework

Develop a web framework (or web framework integration layer) that
uses affairon as its core extension mechanism: request lifecycle
as affairs, middleware as callbacks, plugin-based route registration.
