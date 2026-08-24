"""Algebraic effect system interface."""

from __future__ import annotations

import functools
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

from .core import reset
from .handlers import _current_handler

T = TypeVar("T")


class Effect:
    """Base class for user-defined effect operations."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(args={self.args}, kwargs={self.kwargs})"


async def perform(effect_req: Any) -> Any:
    """Dispatches an effect request to the current dynamic handler."""
    handler = _current_handler.get()
    if handler is not None:
        return handler.handle(effect_req)
    return None


def effectful[**P, R](func: Callable[P, Coroutine[Any, Any, R]]) -> Callable[P, Coroutine[Any, Any, R]]:
    """Decorator to mark a coroutine function as effectful."""

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return await func(*args, **kwargs)

    return wrapper


async def run_effect[R](
    coro_or_func: Callable[..., Any] | Coroutine[Any, Any, R],
    handler: Any,
    *args: Any,
    **kwargs: Any,
) -> R:
    """Executes an effectful computation within the dynamic scope of a handler."""
    token = _current_handler.set(handler)
    try:
        return await reset(coro_or_func, *args, **kwargs)  # type: ignore[no-any-return]
    finally:
        _current_handler.reset(token)