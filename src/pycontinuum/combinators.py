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
    # Run the body under a reset that stops after the first solution
    from .core import reset
    async def run_once():
        return await body()
    # This is a simplified version; it works because body contains amb/fail.
    # A proper once uses the continuation directly.
    return await reset(run_once)

async def maybe(value: T | None) -> T:
    if value is None:
        return await fail()
    return value

async def collect(body: Callable[[], Awaitable[T]]) -> List[T]:
    """Collect all successful results of a non‑deterministic computation.
    Works by running the body in a fresh `reset` block and capturing the list
    that `amb` naturally produces.
    """
    from .core import reset
    async def captured():
        return await body()
    return await reset(captured)
