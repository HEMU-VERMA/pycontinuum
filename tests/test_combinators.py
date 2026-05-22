"""Tests for non‑deterministic and probabilistic combinators."""

import pytest
from pycontinuum.combinators import amb, fail, flip, once, maybe

from pycontinuum.core import reset

@pytest.mark.asyncio
async def test_amb_and_fail():
    async def only_evens():
        x = await amb(1, 2, 3, 4, 5)
        if x % 2 != 0:
            await fail()
        return x
    result = await reset(only_evens)
    assert result == [2, 4]

@pytest.mark.asyncio
async def test_maybe():
    async def safe(val):
        v = await maybe(val)
        return v
    r1 = await reset(safe(42))
    assert r1 == 42
    r2 = await reset(safe(None))
    assert r2 == []   # fail() returns empty list

@pytest.mark.asyncio
async def test_flip_weights():
    async def coin():
        return await flip(0.2)
    # The result is a list of (bool, weight) pairs
    results = await reset(coin)
    true_weight = sum(w for v, w in results if v is True)
    false_weight = sum(w for v, w in results if v is False)
    assert abs(true_weight - 0.2) < 1e-9
    assert abs(false_weight - 0.8) < 1e-9

@pytest.mark.asyncio
async def test_once():
    async def many():
        x = await amb(100, 200, 300)
        return x
    first = await reset(lambda: once(many))
    assert first == 100
