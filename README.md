# PyContinuum

**Multi‑shot delimited continuations with static effect typing for Python 3.12+**

PyContinuum brings **delimited continuations** and **algebraic effects** to Python. Write business logic free of infrastructure concerns, test with pure mock handlers, and run in production with built‑in retries, circuit breakers, and distributed sagas.

---

## 🚀 Why PyContinuum?

- **Multi‑shot continuations** – Pause a function, copy its state, resume it multiple times with different values.
- **Algebraic effects** – Declare side effects as types and swap interpreters for testing, production, or cloud.
- **Static effect typing** – Custom mypy plugin catches missing handlers at compile time.
- **Production resilience** – Retry, circuit breaker, timeout, fallback, saga, dead‑letter queue.
- **Serializable workflows** – Continuations are pure data; save them to disk and resume later.
- **Zero hard dependencies** – Core is pure Python + anyio; extras for tracing and cloud.

---

## 📦 Installation

You need **Python 3.12 or later**.

### Basic Installation

```bash
pip install pycontinuum
```

### With Development Tools (testing, linting, documentation)

```bash
pip install pycontinuum[dev]
```

---

## ⚡ Quick Example

```python
import asyncio
from pycontinuum import reset, amb, fail

async def solve():
    a = await amb(1, 2, 3)
    b = await amb(4, 5, 6)
    if a + b != 7:
        await fail()
    return (a, b)

asyncio.run(reset(solve))  # [(1,6), (2,5), (3,4)]
```

---

## 📚 Features

### Core
- `reset`, `shift`, `Continuation` – replay‑based multi‑shot continuations.

### Combinators
- `amb`, `fail`, `flip`, `once`, `maybe`, `collect` – non‑deterministic & probabilistic search.

### Effects
- `effectful`, `perform`, `Effect` – type‑safe algebraic effects.

### Handlers
- `StateHandler`, `ConsoleHandler` – batteries included.

### Resilience
- `retry`, `circuit_breaker`, `timeout`, `fallback`, `saga`, `dlq`, `bulkhead`, `rate_limit` – production‑ready patterns.

### Security
- Secret redaction, safe JSON serialization, runtime type validation.

### Observability
- OpenTelemetry tracing, Prometheus metrics, structured logging.

---

## 🎯 Core Concepts

### The Idea: Delimited Continuations

Imagine pausing a function halfway through, freezing its state, and later resuming it multiple times with different values. That's a **multi‑shot delimited continuation**.

```python
import asyncio
from pycontinuum import reset, shift

async def ask_name():
    # shift pauses and passes control to a handler
    name = await shift(lambda k: k("World"))
    return f"Hello, {name}!"

result = await asyncio.run(reset(ask_name))
# Hello, World!
```

### How It Works

1. `reset(ask_name)` starts the computation
2. `await shift(...)` suspends and calls the handler (the lambda)
3. The handler receives a **continuation** `k` – the frozen rest of the function
4. Calling `k("World")` resumes the function with "World" as the name
5. The handler can call `k` multiple times, running the function from that point each time

```python
async def choose():
    x = await shift(lambda k: [k(10), k(20)])
    return x

results = await asyncio.run(reset(choose))
# [10, 20] – the handler called k twice!
```

---

## 🔧 Core API

### `reset(coro_func, *args, **kwargs) -> B`

Creates a delimited boundary. The coro_func must be an async generator that yields `Shift` objects. Returns the final result.

```python
result = await reset(my_async_function)
```

### `shift(handler) -> A`

Suspends the computation and calls handler with the current `Continuation`. The handler may call the continuation zero or more times.

```python
value = await shift(lambda k: k(42))
```

### `Continuation[A, B]`

Represents the frozen rest of the computation.

**Methods:**
- `async def __call__(self, value: A) -> B` – Resume with a value
- `async def throw(self, exc: BaseException) -> B` – Resume with an exception

```python
result = await continuation(value)
result = await continuation.throw(ValueError("error"))
```

---

## 🎲 Combinators

### `amb(*choices) -> T`

Non‑deterministically choose one value from multiple choices. Returns a list of all successful results.

```python
async def find():
    x = await amb(1, 2, 3, 4, 5)
    y = await amb(1, 2, 3, 4, 5)
    if x * y != 6:
        await fail()
    return (x, y)

results = await reset(find)
# [(1, 6), (2, 3), (3, 2), (6, 1)]
```

### `fail() -> T`

Prune the current branch (returns empty list).

```python
if condition_fails:
    await fail()  # This branch is discarded
```

### `flip(p: float = 0.5) -> bool`

Probabilistic branching. Returns a list of `(value, weight)` pairs.

```python
async def two_flips():
    a = await flip(0.6)  # True with 60% weight
    b = await flip(0.4)
    return (a, b)

results = await reset(two_flips)
# [((True, True), 0.24), ((True, False), 0.36), ...]
```

### `once(body) -> T`

Run the body and return only the first successful result.

```python
result = await once(find)  # Just the first valid combination
```

### `maybe(value: Optional[T]) -> T`

Fail if the value is `None`; otherwise return it.

```python
x = await amb(1, None, 3)
v = await maybe(x)  # None branch is pruned
```

---

## 🎯 Algebraic Effects

Effects let you declare what your code needs without actually implementing it. This makes code testable and composable.

### Defining an Effect

```python
from pycontinuum import Effect

class Database(Effect):
    async def query(sql: str) -> Any: ...
    async def execute(sql: str) -> None: ...
```

### Using `perform` to Request an Effect

```python
from pycontinuum import perform

async def get_user(user_id: int):
    user = await perform(Database.query(f"SELECT * FROM users WHERE id={user_id}"))
    return user
```

### Writing a Handler

```python
from pycontinuum.handlers import Handler

class MockDatabaseHandler(Handler):
    async def handle(self, request, cont):
        if request.method == "query":
            return await cont({"id": 1, "name": "Alice"})
        elif request.method == "execute":
            return await cont(None)
```

### Using the Handler

```python
from pycontinuum.handlers import _current_handler

token = _current_handler.set(MockDatabaseHandler())
result = await reset(get_user, 1)
_current_handler.reset(token)
```

---

## 💪 Resilience

PyContinuum provides production‑ready resilience patterns that work across continuations.

### `retry(attempts, backoff, jitter)`

Automatically retry on failures.

```python
from pycontinuum.resilience import retry

async with retry(attempts=3, backoff=0.5, jitter=0.1):
    response = await perform(http.get("https://api.example.com/data"))
```

### `circuit_breaker(name, max_failures, reset_timeout)`

Prevent cascading failures.

```python
from pycontinuum.resilience import circuit_breaker, CircuitOpenError

async with circuit_breaker("db-primary", max_failures=5, reset_timeout=30):
    data = await perform(db.query("SELECT ..."))
```

### `timeout(seconds)`

Limit execution time.

```python
from pycontinuum.resilience import timeout

async with timeout(5.0):
    result = await perform(slow_effect())
```

### `fallback(primary, secondary)`

Try primary, fall back to secondary on failure.

```python
from pycontinuum.resilience import fallback

result = await fallback(
    lambda: perform(primary()),
    lambda: perform(secondary())
)
```

### `saga` – Distributed Transactions

Execute steps with automatic compensation on failure.

```python
from pycontinuum.resilience import saga
from pycontinuum import effectful

@saga
@effectful
async def book_trip(user, flight_id, hotel_id):
    flight = await perform(flights.reserve(flight_id))
    hotel = await perform(hotels.reserve(hotel_id))
    payment = await perform(payments.charge(user, flight.price + hotel.price))
    return payment.id
```

If `payments.charge` fails, the saga automatically compensates: `flight.compensate()` and `hotel.compensate()` are called in reverse order.

### `dlq(queue_name)` – Dead‑Letter Queue

Push failed continuations for later inspection.

```python
from pycontinuum.resilience import dlq

async with dlq("order-processing-failures"):
    await perform(process_order(order))
```

### `bulkhead(name, max_concurrent)`

Limit concurrent executions.

```python
from pycontinuum.resilience import bulkhead

async with bulkhead("db-pool", max_concurrent=10):
    await perform(db.query(...))
```

### `rate_limit(name, max_per_second)`

Throttle request rate.

```python
from pycontinuum.resilience import rate_limit

async with rate_limit("api", max_per_second=100):
    await perform(http.get(...))
```

---

## 🔒 Security

### `Secret(value)`

Wrap sensitive values to prevent exposure in serialized forms.

```python
from pycontinuum.security import Secret

api_key = Secret("my-secret-key")
```

### Safe Serialization

Use JSON-based serialization instead of pickle.

```python
from pycontinuum.serialization import dumps, loads

json_bytes = dumps(continuation)
cont2 = loads(json_bytes, allowed_modules={"myapp.workflows"})
```

### Runtime Type Validation

```python
from pycontinuum.security import validate_continuation_input

validate_continuation_input(cont, 42)  # Raises if type mismatch
```

---

## 📊 Observability

### OpenTelemetry Tracing

```python
from pycontinuum.observability import instrument

instrument("order-service")
```

Automatically wraps every `reset` and `Continuation.__call__` with OpenTelemetry spans.

### Prometheus Metrics

Exposes counters and histograms for:
- Continuation resumes (success/error)
- Effect calls (by effect name and method)
- Branch exploration (amb calls)
- Continuation block duration

### Structured Logging

Integrates with `structlog` for context-aware logging with trace IDs.

---

## 🌥️ Real‑World Examples

### Solving Logic Puzzles

**Map Coloring Problem:**

```python
colors = ["red", "green", "blue"]

async def color_map(regions):
    coloring = {}
    for region in regions:
        coloring[region] = await amb(*colors)
        # Constraint: adjacent regions can't share a color
        for neighbor in region.adjacent:
            if neighbor in coloring and coloring[neighbor] == coloring[region]:
                await fail()
    return coloring

solution = await reset(color_map, regions_list)
```

### Order‑Fulfillment Saga

```python
@saga
@effectful
async def fulfill_order(order_id):
    inventory = await perform(Inventory.reserve(order_id.items))
    payment = await perform(Payment.charge(order_id.customer, order_id.total))
    shipment = await perform(Shipping.create_label(order_id, payment.id))
    await perform(Email.send(order_id.customer, "Your order has shipped!"))
    return shipment.tracking_id
```

If any step fails, compensation is automatic.

---

## 🧪 Testing

Testing is simple because you can replace handlers with mocks:

```python
async def test_get_user():
    async def mock_db_query(k):
        return await k({"id": 1, "name": "Test"})
    
    async def logic():
        user = await shift(mock_db_query)
        return user
    
    result = await reset(logic)
    assert result == {"id": 1, "name": "Test"}
```

For effects, set a mock handler via context:

```python
from pycontinuum.handlers import _current_handler

token = _current_handler.set(mock_handler)
result = await reset(my_effectful_func)
_current_handler.reset(token)
```

---

## 📖 API Reference

### Core Module

| Function | Signature | Description |
|----------|-----------|-------------|
| `reset` | `reset(coro_func, *args, **kwargs) -> B` | Create a delimited boundary |
| `shift` | `shift(handler) -> A` | Suspend and hand control to handler |
| `abort` | `abort(exc: BaseException) -> NoReturn` | Abort the current continuation |

### Combinators Module

| Function | Return | Description |
|----------|--------|-------------|
| `amb` | `[T]` | Non‑deterministic choice |
| `fail` | `[]` | Prune current branch |
| `flip` | `[(bool, float)]` | Probabilistic branch |
| `once` | `T` | First successful result |
| `maybe` | `T` | Fail if None |

### Resilience Module

| Function | Type | Description |
|----------|------|-------------|
| `retry` | context manager | Retry with backoff |
| `circuit_breaker` | context manager | Prevent cascading failures |
| `timeout` | context manager | Enforce time limit |
| `fallback` | callable | Primary + secondary |
| `saga` | decorator | Distributed transaction |
| `dlq` | context manager | Dead‑letter queue |
| `bulkhead` | context manager | Concurrency limit |
| `rate_limit` | context manager | Rate limit |

---

## ❓ FAQ

**Q: Is PyContinuum production‑ready?**  
A: The core engine is stable and extensively tested. The effect system and some resilience combinators are under active development. Use the core and combinators with confidence.

**Q: How does this compare to asyncio or trio?**  
A: It's built on top of anyio (which wraps asyncio/trio). It doesn't replace them; it adds a higher‑level abstraction for control flow and side effects.

**Q: Can I use this in a web framework like FastAPI?**  
A: Yes! Use `reset`/`shift` inside async endpoints. Effect handlers can be set per request via context variables.

**Q: Why delimited continuations instead of generators?**  
A: Generators can only yield to their immediate caller. Delimited continuations capture the entire rest of the computation and invoke it from anywhere, making them much more powerful.

**Q: How do I handle errors in sagas?**  
A: Compensation is automatic. If any step fails, all previous steps' compensation functions are called in reverse order.

---

## 🤝 Contributing

We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

In short:
- All code must pass `ruff check` and `mypy --strict`
- Tests must have 100% coverage
- Write Google‑style docstrings

---

## 📄 License

Apache 2.0

---

## 📚 Learn More

- [Full Documentation](#) – Comprehensive guide and tutorials
- [Examples](#) – Real‑world patterns and use cases
- [API Reference](#) – Complete function and class documentation

---

**Happy effectful programming!** 🎉
