# Search & Logic

Continuation branching can solve small constraint problems.

```python
import asyncio
from pycontinuum import reset, amb, fail

async def find():
    x = await amb(1, 2, 3, 4, 5)
    y = await amb(1, 2, 3, 4, 5)
    if x * y != 6:
        await fail()
    return x, y

print(asyncio.run(reset(find)))
```

`amb` creates branches and `fail` prunes invalid ones.
