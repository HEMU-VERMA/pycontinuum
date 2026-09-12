# Effects & Handlers

Effects let business logic request an operation without deciding how it is implemented.

## The architecture

1. **Business logic** describes what it needs.
2. **Effect requests** represent operations.
3. **Handlers** implement those operations.

This separation makes tests easier because production adapters can be replaced with deterministic handlers.

## Effect API

PyContinuum exposes `Effect`, `perform`, and `effectful` for effect-oriented application code.

## Built-in handlers

- `StateHandler` — simple get/put state behavior.
- `Console` — console-print behavior.

## Replay safety

Keep network calls, persistence, queues, and other irreversible operations behind explicit handlers. Replay should reproduce computation without accidentally duplicating an external side effect.
