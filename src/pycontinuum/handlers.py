"""Built‑in effect handlers."""

from __future__ import annotations
import contextvars
from typing import Any, Dict, Type, Optional
from .core import Continuation, shift, reset
from .effect import EffectRequest

_current_handler: contextvars.ContextVar[Optional["Handler"]] = contextvars.ContextVar("_current_handler", default=None)

def _set_current_handler(handler: Handler):
    _current_handler.set(handler)

def _get_current_handler() -> Handler | None:
    return _current_handler.get()

class Handler:
    """Base class for effect handlers."""
    async def handle(self, request: EffectRequest, cont: Continuation) -> Any:
        raise NotImplementedError

class StateHandler(Handler):
    """Handler for state effects (get/put)."""
    def __init__(self, initial):
        self._state = initial

    async def handle(self, request: EffectRequest, cont: Continuation) -> Any:
        if request.method == "get":
            return await cont(self._state)
        elif request.method == "put":
            self._state = request.args[0]
            return await cont(None)
        raise ValueError(f"Unknown state operation: {request.method}")

# For console effects
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

# Pre‑instantiated console handler for convenience
class Console:
    """Effect for console I/O."""
    read = staticmethod(lambda prompt: EffectRequest(Console, "read", (prompt,), {}))
    write = staticmethod(lambda msg: EffectRequest(Console, "write", (msg,), {}))