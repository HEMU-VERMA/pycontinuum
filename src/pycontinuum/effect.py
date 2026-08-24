"""Algebraic effect system interface."""

from __future__ import annotations

from typing import Any

from .handlers import _current_handler


async def perform(effect_req: Any) -> Any:
    """Dispatches an effect request to the current dynamic handler."""
    handler = _current_handler.get()
    if handler is not None:
        return handler.handle(effect_req)
    return None