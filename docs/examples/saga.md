# Saga Transactions

Sagas model multi-step workflows where earlier actions may need compensation if a later step fails.

```python
from pycontinuum.resilience import saga

@saga
async def book_trip(user, flight_id, hotel_id):
    # Keep external operations and compensation explicit.
    ...
```

For production workflows, make external operations idempotent and define compensating actions for already-committed steps.
