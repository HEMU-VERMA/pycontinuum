"""Tests for resilience combinators."""

import pytest
from pycontinuum.resilience import retry, circuit_breaker, CircuitOpenError
class FailingCall:
    def __init__(self, fail_count):
        self.attempts = 0
        self.fail_count = fail_count
    async def call(self):
        self.attempts += 1
        if self.attempts <= self.fail_count:
            raise ConnectionError("temporary")
        return "success"

@pytest.mark.asyncio
async def test_retry_success():
    flaky = FailingCall(fail_count=2)
    async with retry(attempts=3, backoff=0.01):
        result = await flaky.call()
    assert result == "success"
    assert flaky.attempts == 3

@pytest.mark.asyncio
async def test_circuit_breaker_opens():
    async with circuit_breaker("test", max_failures=1, reset_timeout=0.1):
        raise ConnectionError("fail")
    # Next attempt should raise CircuitOpenError
    with pytest.raises(CircuitOpenError):
        async with circuit_breaker("test", max_failures=1, reset_timeout=0.1):
            pass
