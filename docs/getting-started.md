# Getting Started

## Requirements

- Python **3.12+**
- A virtual environment is recommended for development.

## Install

Create an environment and install the package:

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install pycontinuum
```

For development tools:

```bash
pip install "pycontinuum[dev]"
```

## Hello, continuation

```python
import asyncio
from pycontinuum import reset, shift

async def hello():
    name = await shift(lambda k: k("World"))
    return f"Hello, {name}!"

print(asyncio.run(reset(hello)))
```

`reset` creates a delimited boundary. `shift` suspends the computation and gives a handler a `Continuation` for the rest of the computation.

## Multiple resumes

A continuation can be invoked more than once:

```python
async def choose():
    value = await shift(lambda k: [k(10), k(20)])
    return value
```

This replay-oriented model makes nondeterministic search possible without turning application code into a custom state machine.

## Development

Run the same checks used by CI:

```bash
ruff check .
mypy --strict src
pytest
```

Build the documentation locally:

```bash
mkdocs serve
```

Then open the local address printed by MkDocs.

## Next steps

1. Read [Core Concepts](core-concepts.md).
2. Try [Combinators](combinators.md).
3. Learn about [Effects & Handlers](effects.md).
4. Review [Resilience](resilience.md).
5. Browse the [API Reference](api-reference/core.md).
