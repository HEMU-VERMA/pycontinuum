# PyContinuum

**Multi-shot delimited continuations and algebraic effects for modern Python.**

PyContinuum is an async-first Python library for capturing, replaying, and composing delimited continuations. It also provides search combinators, effect helpers, and resilience utilities.

## Install on macOS

PyContinuum targets Python 3.12+.

~~~bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pycontinuum
~~~

You do not need to clone the repository to install it.

## First program

~~~python
import asyncio
from pycontinuum import reset, shift

async def hello():
    name = await shift(lambda k: k("World"))
    return f"Hello, {name}!"

print(asyncio.run(reset(hello)))
~~~

reset establishes the boundary. shift captures the remainder and gives a Continuation to its handler.

## Branching

~~~python
import asyncio
from pycontinuum import reset, shift

async def choose():
    value = await shift(lambda k: [k(10), k(20)])
    return value

print(asyncio.run(reset(choose)))
~~~

A continuation can be resumed more than once.

## Main features

- Delimited continuations
- Multi-shot replay
- Nondeterministic search
- Probabilistic branching
- Effect-oriented application architecture
- Retry, circuit breaker, timeout and fallback helpers
- Type information for mypy users

## Documentation

- [Getting Started](getting-started.md)
- [Core Concepts](core-concepts.md)
- [Combinators](combinators.md)
- [Effects & Handlers](effects.md)
- [Resilience](resilience.md)
- [Cloud Runtime](cloud.md)
- [API Reference](api-reference/core.md)
- [Examples](examples/search.md)

## Type checking

Users can install mypy separately:

~~~bash
python -m pip install mypy
mypy your_program.py
~~~

Contributors can install the development extra and run mypy against the package.

[GitHub repository](https://github.com/HEMU-VERMA/pycontinuum) · [PyPI](https://pypi.org/project/pycontinuum/)
