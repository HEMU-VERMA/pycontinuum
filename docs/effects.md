# Effects & Handlers

Effects let business logic request an operation without deciding how that operation is implemented.

## The architecture

Think of an effectful application as three layers:

1. **Business logic** — describes what it needs.
2. **Effect request** — represents an operation.
3. **Handler** — performs that operation in the current environment.

This separation makes tests easier because production adapters can be replaced with deterministic handlers.

## Effect API

The package exposes `Effect`, `perform`, and `effectful` for effect-oriented code.

A conceptual effect might look like:

```python
class Database(Effect):
    async def query(sql: str): ...
```

Application code can then request the operation without embedding database-specific setup.

## Built-in handlers

The handlers module includes:

- `StateHandler` — simple get/put state behavior.
- `Console` — a small console-print handler.

## Testing

Prefer a fake handler in tests:

```python
# Production and tests can provide different implementations
# while the business workflow stays unchanged.
```

## Handler boundaries

Keep network calls, persistence, queues, and other irreversible operations behind handlers. This is particularly important with replay-based continuations: replay should reproduce computation, not accidentally duplicate an external side effect.
