import pytest
from pycontinuum import reset, shift, amb, fail, Continuation

@pytest.mark.asyncio
async def test_basic_shift_reset():
    async def greet():
        name = await shift(lambda k: k("World"))
        return f"Hello, {name}!"
    result = await reset(greet)
    assert result == "Hello, World!"

@pytest.mark.asyncio
async def test_amb_all_branches():
    async def puzzle():
        a = await amb(1, 2)
        b = await amb(3, 4)
        return (a, b)
    result = await reset(puzzle)
    assert result == [(1,3), (1,4), (2,3), (2,4)]

@pytest.mark.asyncio
async def test_fail_removes_branch():
    async def only_even():
        x = await amb(1,2,3,4)
        if x % 2 != 0:
            await fail()
        return x
    result = await reset(only_even)
    assert result == [2,4]