# Getting Started

## Requirements

- Python 3.12 or newer
- macOS, Linux, or Windows
- A virtual environment is recommended

## Install on macOS

~~~bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pycontinuum
~~~

With Homebrew Python:

~~~bash
brew install python@3.12
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install pycontinuum
~~~

## Install development tools

~~~bash
python -m pip install "pycontinuum[dev]"
~~~

This installs testing, linting, type checking, and documentation tools.

## First continuation

~~~python
import asyncio
from pycontinuum import reset, shift

async def greet():
    name = await shift(lambda k: k("World"))
    return f"Hello, {name}!"

print(asyncio.run(reset(greet)))
~~~

## Resume multiple times

~~~python
import asyncio
from pycontinuum import reset, shift

async def choose():
    value = await shift(lambda k: [k("A"), k("B")])
    return value

print(asyncio.run(reset(choose)))
~~~

The same continuation is replayed for both values.

## Search

~~~python
import asyncio
from pycontinuum import reset, amb, fail

async def solve():
    x = await amb(1, 2, 3, 4, 5)
    y = await amb(1, 2, 3, 4, 5)
    if x * y != 6:
        await fail()
    return x, y

print(asyncio.run(reset(solve)))
~~~

## Development checks

~~~bash
ruff check .
mypy src
pytest
~~~

## Build documentation locally

~~~bash
mkdocs serve
~~~

Then open the local URL printed by MkDocs.

## Next

Continue with [Core Concepts](core-concepts.md), then [Combinators](combinators.md), [Effects & Handlers](effects.md), and [Resilience](resilience.md).
