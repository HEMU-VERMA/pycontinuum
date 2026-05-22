"""Tests for built‑in handlers."""

import pytest
from pycontinuum.handlers import StateHandler

@pytest.mark.asyncio
async def test_state_handler_manual():
    handler = StateHandler(10)
    # Simulate a direct continuation call
    from pycontinuum.core import shift

    async def get_twice():
        a = await shift(lambda k: handler.handle(StateHandler.get_request(), k))
        b = await shift(lambda k: handler.handle(StateHandler.get_request(), k))
        return a + b
    # We need StateHandler.get_request() to be an EffectRequest... not yet.
    # This test will be adjusted once effect.py is fully integrated.
    pass
