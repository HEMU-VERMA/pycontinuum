"""Core engine for delimited continuations via replay."""

from __future__ import annotations
import asyncio
from typing import (TypeVar, Generic, Callable, Awaitable, AsyncGenerator,
                    Any, NoReturn, Optional)

A = TypeVar("A")
B = TypeVar("B")

class Shift(Awaitable[A], Generic[A, B]):
    """Suspends the computation and yields control to a handler."""
    def __init__(self, handler: Callable[[Continuation[A, B]], Awaitable[B]]) -> None:
        self._handler = handler
        self._done = asyncio.Event()
        self._value: Optional[A] = None
        self._exception: Optional[BaseException] = None
        self._is_exception = False

    def set_value(self, value: A) -> None:
        self._value = value
        self._is_exception = False
        self._done.set()

    def set_exception(self, exc: BaseException) -> None:
        self._exception = exc
        self._is_exception = True
        self._done.set()

    def __await__(self):
        yield self
        if self._is_exception:
            raise self._exception  # pylint: disable=raising-bad-type
        return self._value

class Continuation(Generic[A, B]):
    """A captured delimited continuation that can be invoked with a value."""
    def __init__(self, func: Callable[..., AsyncGenerator[Shift, A]],
                 args: tuple, kwargs: dict, history: tuple) -> None:
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._history = history

    @property
    def history(self) -> tuple:
        return self._history

    async def __call__(self, value: A) -> B:
        decisions = list(self._history) + [value]
        return await _replay_and_continue(self._func, self._args, self._kwargs, decisions)

    async def throw(self, exc: BaseException) -> B:
        decisions = list(self._history)
        agen = self._func(*self._args, **self._kwargs)
        idx = 0
        while True:
            try:
                event = await (agen.asend(None) if idx == 0 else agen.asend(decisions[idx-1]))
            except StopAsyncIteration:
                return None  # type: ignore
            if isinstance(event, Shift):
                idx += 1
                if idx > len(decisions):
                    try:
                        await agen.athrow(exc)
                    except StopAsyncIteration:
                        return None  # type: ignore
                    continue
            else:
                return event  # type: ignore

    def __reduce__(self):
        return (Continuation, (self._func, self._args, self._kwargs, self._history))

    def __repr__(self):
        return f"<Continuation history={self._history}>"

async def _replay_and_continue(func, args, kwargs, decisions):
    agen = func(*args, **kwargs)
    idx = 0
    while True:
        try:
            event = await (agen.asend(None) if idx == 0 else agen.asend(decisions[idx-1]))
        except StopAsyncIteration:
            return None
        if isinstance(event, Shift):
            idx += 1
            if idx > len(decisions):
                return await _handle_new_shift(event, func, args, kwargs, tuple(decisions[:idx-1]))
        else:
            return event

async def _handle_new_shift(shift_obj, func, args, kwargs, history):
    cont = Continuation(func, args, kwargs, history)
    return await shift_obj._handler(cont)

async def reset(coro_func: Callable[..., AsyncGenerator[Shift, Any]], *args, **kwargs) -> Any:
    agen = coro_func(*args, **kwargs)
    history: list = []
    while True:
        try:
            event = await (agen.asend(None) if not history else agen.asend(history[-1]))
        except StopAsyncIteration:
            return None
        if isinstance(event, Shift):
            cont = Continuation(coro_func, args, kwargs, tuple(history))
            return await event._handler(cont)
        else:
            return event

async def shift(handler: Callable[[Continuation], Awaitable]) -> Any:
    shift_obj = Shift(handler)
    return await shift_obj

class Abort(BaseException):
    """Exception used to abort a delimited continuation."""

async def abort(exc: BaseException = Abort("continuation aborted")) -> NoReturn:
    async def handler(cont: Continuation) -> NoReturn:
        raise exc
    await shift(handler)
    raise RuntimeError("unreachable")