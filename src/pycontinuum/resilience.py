"""Resilience combinators built on continuations."""

from __future__ import annotations

import asyncio
import contextlib
import random
import time
import types
from collections.abc import Awaitable, Callable
from typing import Any, Self


class _CircuitState:
    CLOSED, OPEN, HALF_OPEN = range(3)


_circuit_registry: dict[str, dict[str, Any]] = {}


class CircuitOpenError(Exception):
    """Raised when a circuit breaker is open."""


class _RetryContextManager:
    def __init__(self, attempts: int, backoff: float, jitter: float) -> None:
        self.attempts = attempts
        self.backoff = backoff
        self.jitter = jitter
        self.current_attempt = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> bool:
        if exc_type is not None and issubclass(exc_type, (ConnectionError, TimeoutError)):
            self.current_attempt += 1
            if self.current_attempt < self.attempts:
                sleep_time = self.backoff * (2 ** (self.current_attempt - 1)) + random.uniform(
                    0, self.jitter
                )
                await asyncio.sleep(sleep_time)
                return True
        return False


def retry(attempts: int = 3, backoff: float = 1.0, jitter: float = 0.0) -> _RetryContextManager:
    return _RetryContextManager(attempts, backoff, jitter)


class _CircuitBreakerContextManager:
    def __init__(self, name: str, max_failures: int = 5, reset_timeout: float = 30.0) -> None:
        self.name = name
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout

    async def __aenter__(self) -> Self:
        state = _circuit_registry.setdefault(
            self.name, {"state": _CircuitState.CLOSED, "failures": 0, "last_open": 0.0}
        )
        if state["state"] == _CircuitState.OPEN:
            if time.monotonic() - state["last_open"] > self.reset_timeout:
                state["state"] = _CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError(f"Circuit {self.name} is OPEN")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> bool:
        state = _circuit_registry.setdefault(
            self.name, {"state": _CircuitState.CLOSED, "failures": 0, "last_open": 0.0}
        )
        if exc_type is None:
            if state["state"] == _CircuitState.HALF_OPEN:
                state["state"] = _CircuitState.CLOSED
            state["failures"] = 0
            return False

        state["failures"] += 1
        if state["failures"] >= self.max_failures:
            state["state"] = _CircuitState.OPEN
            state["last_open"] = time.monotonic()
        return False


def circuit_breaker(
    name: str, max_failures: int = 5, reset_timeout: float = 30.0
) -> _CircuitBreakerContextManager:
    return _CircuitBreakerContextManager(name, max_failures, reset_timeout)


@contextlib.asynccontextmanager
async def timeout(seconds: float):
    import anyio

    with anyio.move_on_after(seconds) as scope:
        yield
        if scope.cancelled_caught:
            raise TimeoutError()


async def fallback[T](
    primary: Callable[[], Awaitable[T]],
    secondary: Callable[[], Awaitable[T]],
) -> T:
    try:
        return await primary()
    except Exception:  # noqa: BLE001
        return await secondary()


def saga(func: Callable[..., Any]) -> Callable[..., Any]:
    func._is_saga = True  # type: ignore[attr-defined]
    return func


class _DlqContextManager:
    def __init__(self, queue_name: str) -> None:
        self.queue_name = queue_name

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> bool:
        return False


def dlq(queue_name: str) -> _DlqContextManager:
    return _DlqContextManager(queue_name)