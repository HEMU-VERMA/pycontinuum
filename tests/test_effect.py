"""Tests for the algebraic effect system."""

import pytest
from pycontinuum.effect import perform  # only used
from pycontinuum.handlers import StateHandler, _current_handler
from pycontinuum.core import reset

@pytest.mark.asyncio
async def test_state_handler():
    state = StateHandler(0)
    async def counter():
        v = await perform(StateHandler.get())   # simulated via request
        await perform(StateHandler.put(v+1))
        return await perform(StateHandler.get())
    # set up handler
    token = _current_handler.set(state)
    try:
        result = await reset(counter)
        assert result == 1
    finally:
        _current_handler.reset(token)

# Additional tests for console (with mocking input/output) etc.
