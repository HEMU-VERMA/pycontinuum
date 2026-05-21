"""Resilience combinators built on continuations."""

from __future__ import annotations
import time
import random
import contextlib
from typing import Any, Callable, Awaitable
from .core import shift, reset, Continuation

# Retry context manager
@contextlib.asynccontextmanager
async def retry(attempts: int = 3, backoff: float = 1.0, jitter: float = 0.0):
    for i in range(attempts):
        try:
            yield
            break
        except (ConnectionError, TimeoutError) as e:
            if i == attempts - 1:
                raise
            sleep_time = backoff * (2 ** i) + random.uniform(0, jitter)
            await __import__("asyncio").sleep(sleep_time)

# Circuit breaker state (simplified)
class _CircuitState:
    CLOSED, OPEN, HALF_OPEN = range(3)

@contextlib.asynccontextmanager
async def circuit_breaker(name: str, max_failures: int = 5, reset_timeout: float = 30):
    # Use global state for demo (replace with proper registry)
    state = _circuit_registry.setdefault(name, {"state": _CircuitState.CLOSED, "failures": 0, "last_open": 0})
    if state["state"] == _CircuitState.OPEN:
        if time.monotonic() - state["last_open"] > reset_timeout:
            state["state"] = _CircuitState.HALF_OPEN
        else:
            raise CircuitOpenError(f"Circuit {name} is OPEN")
    try:
        yield
        if state["state"] == _CircuitState.HALF_OPEN:
            state["state"] = _CircuitState.CLOSED
        state["failures"] = 0
    except Exception:
        state["failures"] += 1
        if state["failures"] >= max_failures:
            state["state"] = _CircuitState.OPEN
            state["last_open"] = time.monotonic()
        raise

_circuit_registry = {}

class CircuitOpenError(Exception):
    pass

@contextlib.asynccontextmanager
async def timeout(seconds: float):
    import anyio
    with anyio.move_on_after(seconds) as scope:
        yield
        if scope.cancelled_caught:
            raise TimeoutError()

async def fallback(primary: Callable[[], Awaitable], secondary: Callable[[], Awaitable]) -> Any:
    try:
        return await primary()
    except Exception:
        return await secondary()

# Saga and DLQ stubs (full implementation requires more infrastructure)
def saga(func):
    func._is_saga = True
    return func

@contextlib.asynccontextmanager
async def dlq(queue_name: str):
    try:
        yield
    except Exception as e:
        # In real code, publish to queue
        raise