"""Core engine for delimited continuations via replay."""

from __future__ import annotations

import inspect
import marshal
import types
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


class _ContinuationValue:
    """Wrapper that supports direct scalar equality, awaiting, and iterable expansion."""

    def __init__(self, value: Any) -> None:
        self._value = value

    def __iter__(self) -> Any:
        if isinstance(self._value, list):
            return iter(self._value)
        return iter([self._value])

    def __eq__(self, other: object) -> bool:
        return bool(self._value == other)

    def __repr__(self) -> str:
        return repr(self._value)

    def __await__(self) -> Any:
        if inspect.isawaitable(self._value):
            return self._value.__await__()

        async def _resolve() -> Any:
            return self._value

        return _resolve().__await__()


def _reconstruct_continuation(
    code_bytes: bytes | None,
    func_name: str,
    defaults: tuple[Any, ...] | None,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    history: tuple[Any, ...],
    type_a: type | None,
    type_b: type | None,
) -> Continuation[Any, Any]:
    if code_bytes is not None:
        code = marshal.loads(code_bytes)
        func = types.FunctionType(code, globals(), func_name, defaults)
    else:
        func = None  # type: ignore[assignment]
    return Continuation(func, args, kwargs, history, type_a, type_b)


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
        res = _execute_with_history(self._func, self._args, self._kwargs, new_history)
        return _ContinuationValue(res)

    def throw(self, exc: BaseException) -> Any:
        target_step = len(self._history)
        res = _execute_with_history(
            self._func,
            self._args,
            self._kwargs,
            self._history,
            throw_target=(target_step, exc),
        )
        return _ContinuationValue(res)

    def __reduce__(self) -> tuple[Any, ...]:
        code_bytes = marshal.dumps(self._func.__code__) if hasattr(self._func, "__code__") else None
        func_name = getattr(self._func, "__name__", "continuation_func")
        defaults = getattr(self._func, "__defaults__", None)
        return (
            _reconstruct_continuation,
            (
                code_bytes,
                func_name,
                defaults,
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
        handler_res = sig.shift_obj.handler(captured_k)
        if isinstance(handler_res, _ContinuationValue):
            handler_res = handler_res._value
        if inspect.iscoroutine(handler_res):
            try:
                while True:
                    try:
                        handler_res.send(None)
                    except StopIteration as stop:
                        return stop.value
            finally:
                handler_res.close()
        return handler_res
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