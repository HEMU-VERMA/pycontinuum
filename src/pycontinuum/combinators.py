"""High‑level combinators for non‑deterministic search."""

from __future__ import annotations
from typing import TypeVar, Callable, Awaitable, List
from .core import shift, Continuation

T = TypeVar("T")

async def amb(*choices: T) -> T:
    async def handler(k: Continuation[T, T]) -> list[T]:
        results = []
        for c in choices:
            results.extend(await k(c))
        return results
    return await shift(handler)

async def fail() -> T:
    return await shift(lambda k: [])

async def flip(p: float = 0.5) -> bool:
    async def handler(k: Continuation[bool, bool]) -> list:
        results = []
        for choice, w in [(True, p), (False, 1 - p)]:
            branch = await k(choice)
            results.extend([(v, weight * w) for v, weight in branch])
        return results
    return await shift(handler)

async def once(body: Callable[[], Awaitable[T]]) -> T:
    async def handler(k: Continuation[None, T]) -> T | None:
        result = await body()
        return result
    return await shift(lambda k: handler(k))

async def maybe(value: T | None) -> T:
    if value is None:
        return await fail()
    return value

async def collect(body: Callable[[], Awaitable[T]]) -> List[T]:
    # Simplified: use amb over a list built by calling body repeatedly
    # (full implementation would use a more efficient mechanism)
    results = []
    async def handler(k: Continuation[None, T]) -> list[T]:
        # For each branch, run body and collect
        # This is a placeholder; see docs for proper `collect`.
        ...
    raise NotImplementedError("collect requires a proper implementation")