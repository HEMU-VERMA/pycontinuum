# PyContinuum

**Multi‑shot delimited continuations with static effect typing for Python 3.12+**

PyContinuum brings **delimited continuations** and **algebraic effects** to Python.  
Write business logic free of infrastructure concerns, test with pure mock handlers, and run in production with built‑in retries, circuit breakers, and distributed sagas.

```bash
pip install pycontinuum

Quick Example

import asyncio
from pycontinuum import reset, amb, fail

async def solve():
    a = await amb(1, 2, 3)
    b = await amb(4, 5, 6)
    if a + b != 7:
        await fail()
    return (a, b)

asyncio.run(reset(solve))  # [(1,6), (2,5), (3,4)]

Core: reset, shift, Continuation – replay‑based multi‑shot continuations.

Combinators: amb, fail, flip, once – non‑deterministic & probabilistic search.

Effects: effectful, perform, Effect – type‑safe algebraic effects.

Handlers: StateHandler, Console, Http, Database – batteries included.

Resilience: retry, circuit_breaker, timeout, fallback, saga – cloud‑native.