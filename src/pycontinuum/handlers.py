"""Built‑in effect handlers."""

from __future__ import annotations
import contextvars
from typing import Any, Optional
from .core import Continuation
from .effect import EffectRequest

_current_handler: contextvars.ContextVar[Optional["Handler"]] = contextvars.ContextVar(
    "_current_handler", default=None
)

def _set_current_handler(handler: "Handler") -> None:
    _current_handler.set(handler)

def _get_current_handler() -> "Handler | None":
    return _current_handler.get()

class Handler:
    """Base class for effect handlers."""
    async def handle(self, request: EffectRequest, cont: Continuation) -> Any:
        raise NotImplementedError

class StateHandler(Handler):
    """Handler for state effects (get/put)."""
    def __init__(self, initial: Any) -> None:
        self._state = initial

    async def handle(self, request: EffectRequest, cont: Continuation) -> Any:
        if request.method == "get":
            return await cont(self._state)
        elif request.method == "put":
            self._state = request.args[0]
            return await cont(None)
        raise ValueError(f"Unknown state operation: {request.method}")

    def get(self) -> EffectRequest:
        return EffectRequest(StateHandler, "get", (), {})

    def put(self, value: Any) -> EffectRequest:
        return EffectRequest(StateHandler, "put", (value,), {})

# Console effect
class ConsoleHandler(Handler):
    async def handle(self, request: EffectRequest, cont: Continuation) -> Any:
        if request.method == "read":
            prompt = request.args[0]
            value = input(prompt)
            return await cont(value)
        elif request.method == "write":
            print(*request.args)
            return await cont(None)
        raise ValueError(f"Unknown console operation: {request.method}")

class Console:
    """Effect for console I/O."""
    @staticmethod
    def read(prompt: str) -> EffectRequest:
        return EffectRequest(ConsoleHandler, "read", (prompt,), {})

    @staticmethod
    def write(msg: str) -> EffectRequest:
        return EffectRequest(ConsoleHandler, "write", (msg,), {})
