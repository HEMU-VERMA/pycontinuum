# Resilience

PyContinuum includes async resilience building blocks for operations that can fail or become slow.

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

A circuit transitions from closed to open after repeated failures and can later probe with a half-open attempt.

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

If the primary operation fails, the secondary callable is used.

## Workflow patterns

The module also exposes `saga`, `dlq`, `bulkhead`, and `rate_limit` for larger workflows. Treat these as infrastructure boundaries and test failure paths explicitly.
