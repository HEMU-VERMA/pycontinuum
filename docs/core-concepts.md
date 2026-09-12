# Core Concepts

## The continuation model

A continuation is the rest of a computation from a particular point onward. PyContinuum uses replay to capture that rest of the computation up to the nearest `reset` boundary.

The important pieces are:

- `reset()` — establishes the delimiter.
- `shift()` — captures the current continuation.
- `Continuation` — represents the captured remainder.
- `abort()` — exits the current delimited computation.

## reset

`reset` accepts an async callable or coroutine and evaluates it inside a fresh execution history:

```python
result = await reset(my_function, argument)
```

## shift

A shift handler receives the continuation:

```python
async def workflow():
    value = await shift(lambda k: k(42))
    return value
```

The handler can decide whether to resume, how many times to resume, and what values to provide.

## Multi-shot behavior

Because resumption replays the computation, the same continuation can be called repeatedly:

```python
async def workflow():
    value = await shift(lambda k: [k("A"), k("B")])
    return value
```

This is the foundation for branching computations.

## Exceptions

A continuation also supports `throw`:

```python
result = await continuation.throw(ValueError("invalid"))
```

Use this when the next execution should receive an exception rather than a normal value.

## Aborting

`abort()` raises an internal control-flow signal that is converted back into the requested exception at the continuation boundary.

## Design guidance

Keep `reset` at a clear application boundary. Capture continuations only around computations that you intend to replay, and keep external side effects behind explicit handlers so replay does not accidentally duplicate infrastructure operations.
