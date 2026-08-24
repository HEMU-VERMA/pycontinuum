"""High‑level combinators for non‑deterministic search."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import Any

from .core import Continuation, reset, shift


async def amb(*choices: Any) -> Any:
    """Non-deterministic choice operator."""

    async def handler(k: Continuation[Any, Any]) -> list[Any]:
        results: list[Any] = []
        for c in choices:
            res = k(c)
            if inspect.isawaitable(res):
                res = await res
            if isinstance(res, list):
                results.extend(res)
            elif res is not None:
                results.append(res)
        return results

    return await shift(handler)


async def fail() -> Any:
    """Prunes the current execution branch."""
    return await shift(lambda k: [])


async def flip(p: float = 0.5) -> Any:
    """Probabilistic binary choice operator."""

    async def handler(k: Continuation[Any, Any]) -> list[tuple[Any, float]]:
        results: list[tuple[Any, float]] = []
        for choice, w in [(True, p), (False, 1.0 - p)]:
            branch = k(choice)
            if inspect.isawaitable(branch):
                branch = await branch
            if isinstance(branch, list):
                for item in branch:
                    if isinstance(item, tuple) and len(item) == 2:
                        v, weight = item
                        results.append((v, weight * w))
                    else:
                        results.append((item, w))
            else:
                results.append((branch, w))
        return results

    return await shift(handler)


async def once[T](body: Callable[[], Awaitable[T]]) -> T:
    """Runs the computation and returns only the first successful result."""
    res = await reset(body)
    if isinstance(res, list) and len(res) > 0:
        return res[0]  # type: ignore[no-any-return]
    return res  # type: ignore[no-any-return]


async def maybe[T](value: T | None) -> T:
    """Unwraps an optional value or prunes the branch if None."""
    if value is None:
        return await fail()  # type: ignore[no-any-return]
    return value


async def collect[T](body: Callable[[], Awaitable[T]]) -> list[T]:
    """Collects all successful branches of a non-deterministic computation."""
    res = await reset(body)
    if isinstance(res, list):
        return res
    return [res]