# Resilience

PyContinuum includes async resilience building blocks.

## Retry

```python
from pycontinuum.resilience import retry

async with retry(attempts=3, backoff=0.5, jitter=0.1):
    await operation()
```

## Circuit breaker

```python
from pycontinuum.resilience import circuit_breaker

async with circuit_breaker("payments", max_failures=5, reset_timeout=30):
    await charge()
```

## Timeout

```python
from pycontinuum.resilience import timeout

async with timeout(5):
    await slow_operation()
```

## Fallback

```python
from pycontinuum.resilience import fallback

result = await fallback(primary, secondary)
```

Additional workflow helpers include `saga`, `dlq`, `bulkhead`, and `rate_limit`.
