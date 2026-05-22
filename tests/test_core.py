"""Tests for the core delimited continuation engine."""

import pytest
from pycontinuum.core import reset, shift, Continuation, abort

# ---------------------------------------------------------------------------
# Basic shift / reset
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_simple_shift_reset():
    async def ask_name():
        name = await shift(lambda k: k("World"))
        return f"Hello, {name}!"
    result = await reset(ask_name)
    assert result == "Hello, World!"

@pytest.mark.asyncio
async def test_shift_without_continuation_call():
    """Handler can ignore the continuation and return a default."""
    async def never_called():
        x = await shift(lambda k: 42)
        return x  # unreachable
    result = await reset(never_called)
    assert result == 42

@pytest.mark.asyncio
async def test_multiple_shifts():
    async def chain():
        a = await shift(lambda k: k(1))
        b = await shift(lambda k: k(2))
        return a + b
    result = await reset(chain)
    assert result == 3

# ---------------------------------------------------------------------------
# Multi‑shot continuations (amb pattern)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_multi_shot():
    async def choose():
        x = await shift(lambda k: [v for c in [10, 20] for v in k(c)])
        return x
    results = await reset(choose)
    assert results == [10, 20]

@pytest.mark.asyncio
async def test_nested_multi_shot():
    async def pick_two():
        a = await shift(lambda k: [v for c in [1, 2] for v in k(c)])
        b = await shift(lambda k: [v for c in [3, 4] for v in k(c)])
        return (a, b)
    results = await reset(pick_two)
    assert results == [(1,3), (1,4), (2,3), (2,4)]

# ---------------------------------------------------------------------------
# Exception propagation
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_exception_in_handler():
    async def body():
        return await shift(lambda k: (_ for _ in ()).throw(ValueError("fail")))
    with pytest.raises(ValueError, match="fail"):
        await reset(body)

@pytest.mark.asyncio
async def test_throw_into_continuation():
    async def cautious():
        try:
            await shift(lambda k: k.throw(ValueError("boom")))
        except ValueError:
            return "caught"
    result = await reset(cautious)
    assert result == "caught"

@pytest.mark.asyncio
async def test_abort():
    async def must_abort():
        await abort(RuntimeError("aborted"))
        return "should not reach"
    with pytest.raises(RuntimeError, match="aborted"):
        await reset(must_abort)

# ---------------------------------------------------------------------------
# Serialization round‑trip
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_continuation_pickle():
    async def fn(x):
        return await shift(lambda k: k(x * 2))
    # Capture a continuation at the shift point
    cont = None
    async def capture():
        nonlocal cont
        cont = Continuation(fn, (5,), {}, ())
        return await shift(lambda k: 0)  # won't be used
    await reset(capture)
    # Now resume via pickle round-trip
    import pickle
    data = pickle.dumps(cont)
    cont2 = pickle.loads(data)
    result = await cont2(10)   # x=5, so 5*2=10?
    # Actually cont was created with args (5,), the history is empty, and `fn` takes `x`.
    # After resume, it replays fn(5) and hits the shift; we feed value=10 -> returns 10*2=20
    assert result == 20
