# PyContinuum

**Multi-shot delimited continuations and algebraic effects for Python 3.12+.**

PyContinuum brings advanced control-flow and effect-handling primitives to ordinary async Python code. It is designed to keep business logic independent from infrastructure while providing practical resilience utilities.

!!! tip "What you get"
    Capture and replay continuations, express nondeterministic search, model effects explicitly, and compose production resilience patterns.

## Features

- **Delimited continuations** — capture the rest of a computation with `shift()` and establish boundaries with `reset()`.
- **Multi-shot execution** — resume the same continuation more than once.
- **Search combinators** — `amb`, `fail`, `flip`, `once`, `maybe`, and `collect`.
- **Effect-oriented architecture** — keep effect requests separate from their handlers.
- **Resilience primitives** — retry, circuit breaker, timeout, fallback, saga, DLQ, bulkhead, and rate limiting.
- **Serialization support** — continuations can be represented as application data with controlled restoration.
- **Async-first** — built around Python's `async`/`await` model.

## Install

```bash
pip install pycontinuum
```

Development installation:

```bash
pip install "pycontinuum[dev]"
```

## Your first continuation

```python
import asyncio
from pycontinuum import reset, shift

async def greet():
    name = await shift(lambda k: k("World"))
    return f"Hello, {name}!"

print(asyncio.run(reset(greet)))
```

The handler receives a continuation representing the remainder of `greet`. Calling it resumes the computation.

## Search example

```python
import asyncio
from pycontinuum import reset, amb, fail

async def solve():
    a = await amb(1, 2, 3)
    b = await amb(4, 5, 6)
    if a + b != 7:
        await fail()
    return a, b

print(asyncio.run(reset(solve)))
```

## Documentation map

| Section | Purpose |
|---|---|
| [Getting Started](getting-started.md) | Install and run your first program |
| [Core Concepts](core-concepts.md) | Understand reset, shift, and continuations |
| [Combinators](combinators.md) | Search and probabilistic programming |
| [Effects & Handlers](effects.md) | Separate effect requests from implementations |
| [Resilience](resilience.md) | Build fault-tolerant async workflows |
| [Cloud Runtime](cloud.md) | Deployment and persistence guidance |
| [API Reference](api-reference/core.md) | Generated API documentation |
| [Examples](examples/search.md) | Practical patterns |

## Project links

- Source: [GitHub](https://github.com/HEMU-VERMA/pycontinuum)
- Package: [PyPI](https://pypi.org/project/pycontinuum/)
- License: Apache 2.0

!!! warning "API status"
    PyContinuum is actively evolving. Check the API reference and release notes before depending on experimental features in production.
