# Probabilistic Programming

`flip` creates weighted boolean branches.

```python
import asyncio
from pycontinuum import reset, flip

async def experiment():
    a = await flip(0.6)
    b = await flip(0.4)
    return a, b

print(asyncio.run(reset(experiment)))
```

Each branch carries a probability weight so downstream computations can preserve the path probability.
