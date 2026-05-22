"""Algebraic effect system with static typing (manual generator mode)."""

from __future__ import annotations
from typing import Any, TypeVar  # removed Callable, Coroutine, Dict, Protocol, runtime_checkable
from .core import shift, reset, Continuation

T = TypeVar("T")

class EffectRequest:
    """Represents a call to an effect method."""
    def __init__(self, effect_cls: type, method: str, args: tuple, kwargs: dict):
        self.effect_cls = effect_cls
        self.method = method
        self.args = args
        self.kwargs = kwargs

class Effect:
    """Base class for effect declarations."""
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for name, method in cls.__dict__.items():
            if name.startswith("_") or not callable(method):
                continue
            setattr(cls, name, staticmethod(lambda *a, _name=name, _cls=cls, **kw: EffectRequest(_cls, _name, a, kw)))

async def perform(request: EffectRequest) -> Any:
    """Suspend the computation and ask the handler to interpret this effect."""
    async def handler(cont: Continuation) -> Any:
        from .handlers import _get_current_handler
        h = _get_current_handler()
        if h is None:
            raise RuntimeError(f"No handler installed for effect {request.effect_cls.__name__}")
        return await h.handle(request, cont)
    return await shift(handler)

def effectful(func):
    """
    Decorator that marks a function as effectful.
    Currently requires the function to be an async generator using `perform`.
    """
    func._is_effectful = True
    return func

async def run_effect(func, *args, **kwargs):
    """
    Run an effectful function with a default handler.
    The handler must be set before calling this.
    """
    # _set_current_handler import removed (unused)
    return await reset(func, *args, **kwargs)
