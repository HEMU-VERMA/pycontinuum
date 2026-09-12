# Combinators

The combinator layer turns continuations into useful search and branching primitives.

## amb

`amb` chooses among values and explores every branch:

```python
x = await amb("red", "green", "blue")
```

When the surrounding computation is reset, successful branches are collected.

## fail

Use `fail` to prune a branch:

```python
if not valid:
    await fail()
```

## Logic search

```python
async def find_pair():
    a = await amb(1, 2, 3, 4, 5)
    b = await amb(1, 2, 3, 4, 5)
    if a * b != 6:
        await fail()
    return a, b

results = await reset(find_pair)
```

## flip

`flip(p)` creates a weighted boolean branch:

```python
result = await flip(0.6)
```

The resulting branches retain weights so downstream computations can combine probabilities.

## once

`once(body)` runs a computation and returns the first successful result instead of retaining every branch.

## maybe

`maybe(value)` returns the value when it is not `None`; a `None` branch is pruned.

## collect

`collect(body)` normalizes successful output into a list, which is useful when the caller wants a stable collection interface.
