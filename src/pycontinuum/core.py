"""Core engine for delimited continuations via replay."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, NoReturn


class _ShiftSignal(BaseException):
    """Internal control flow signal used to unwind the stack to the nearest reset delimiter."""

    def __init__(self, shift_obj: Shift[Any, Any], step_index: int) -> None:
        self.shift_obj = shift_obj
        self.step_index = step_index


class _AbortSignal(BaseException):
    """Internal control flow signal used by abort()."""

    def __init__(self, exc: BaseException) -> None:
        self.exc = exc


class Shift[A, B](Awaitable[A]):
    """Suspends the computation and yields control to a handler."""

    def __init__(self, handler: Callable[[Continuation[A, B]], Any]) -> None:
        self.handler = handler

    def __await__(self) -> Any:
        decision, _ = _ExecutionTracker.get_decision_or_signal(self)
        return decision
        yield  # type: ignore[unreachable]


class _ExecutionTracker:
    _current_history: tuple[Any, ...] = ()
    _step: int = 0
    _throw_target: tuple[int, BaseException] | None = None

    @classmethod
    def get_decision_or_signal(cls, shift_obj: Shift[Any, Any]) -> tuple[Any, int]:
        idx = cls._step
        cls._step += 1

        if cls._throw_target is not None and cls._throw_target[0] == idx:
            target_exc = cls._throw_target[1]
            cls._throw_target = None
            raise target_exc

        if idx < len(cls._current_history):
            return cls._current_history[idx], idx

        raise _ShiftSignal(shift_obj, idx)


class Continuation[A, B]:
    """A captured delimited continuation that can be invoked with a value."""

    def __init__(
        self,
        func: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        history: tuple[Any, ...],
        type_a: type | None = None,
        type_b: type | None = None,
    ) -> None:
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._history = history
        self._type_a = type_a
        self._type_b = type_b

    @property
    def history(self) -> tuple[Any, ...]:
        return self._history

    def __call__(self, value: A) -> Any:
        new_history = self._history + (value,)
        return _execute_with_history(self._func, self._args, self._kwargs, new_history)

    def throw(self, exc: BaseException) -> Any:
        target_step = len(self._history)
        return _execute_with_history(
            self._func,
            self._args,
            self._kwargs,
            self._history,
            throw_target=(target_step, exc),
        )

    def __reduce__(self) -> tuple[Any, ...]:
        return (
            Continuation,
            (
                self._func,
                self._args,
                self._kwargs,
                self._history,
                self._type_a,
                self._type_b,
            ),
        )

    def __repr__(self) -> str:
        return f"<Continuation history={self._history}>"


def _execute_with_history(
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    history: tuple[Any, ...],
    throw_target: tuple[int, BaseException] | None = None,
) -> Any:
    old_history = _ExecutionTracker._current_history
    old_step = _ExecutionTracker._step
    old_throw = _ExecutionTracker._throw_target

    _ExecutionTracker._current_history = history
    _ExecutionTracker._step = 0
    _ExecutionTracker._throw_target = throw_target

    try:
        res = func(*args, **kwargs)
        if inspect.iscoroutine(res):
            try:
                while True:
                    try:
                        res.send(None)
                    except StopIteration as stop:
                        return stop.value
            finally:
                res.close()
        return res
    except _ShiftSignal as sig:
        captured_k = Continuation(func, args, kwargs, history[: sig.step_index])
        return sig.shift_obj.handler(captured_k)
    except _AbortSignal as abort_sig:
        raise abort_sig.exc from None
    finally:
        _ExecutionTracker._current_history = old_history
        _ExecutionTracker._step = old_step
        _ExecutionTracker._throw_target = old_throw


async def reset(
    coro_or_func: Callable[..., Any] | Coroutine[Any, Any, Any],
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Delimited continuation delimiter (reset)."""
    if inspect.iscoroutine(coro_or_func):
        coro = coro_or_func

        def wrapper() -> Any:
            return coro

        func = wrapper
    elif callable(coro_or_func):
        func = coro_or_func
    else:
        raise TypeError(f"Expected coroutine or callable, got {type(coro_or_func)}")

    return _execute_with_history(func, args, kwargs, history=())


async def shift(handler: Callable[[Continuation[Any, Any]], Any]) -> Any:
    """Captures the current continuation up to the nearest enclosing reset."""
    shift_obj: Shift[Any, Any] = Shift(handler)
    return await shift_obj


class Abort(BaseException):
    """Exception used to abort a delimited continuation."""


_DEFAULT_ABORT = Abort("continuation aborted")


async def abort(exc: BaseException = _DEFAULT_ABORT) -> NoReturn:
    """Immediately aborts the delimited computation with the specified exception."""
    raise _AbortSignal(exc)