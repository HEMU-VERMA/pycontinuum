# Effects & Handlers

Effects separate what application code wants to do from how that operation is implemented.

## Architecture

~~~text
Application logic
       |
       v
Effect request
       |
       v
Effect handler
       |
       +---- database
       +---- HTTP service
       +---- queue
       +---- test fake
~~~

The same workflow can therefore use production infrastructure or deterministic test implementations.

## Public API

PyContinuum exports:

- Effect
- effectful
- perform
- run_effect

Effect is the abstraction for an effect request. perform executes a request through the active handling mechanism.

## StateHandler

StateHandler provides simple state operations.

~~~python
from pycontinuum import StateHandler

state = StateHandler(initial_state=0)
request = state.get()
~~~

It is useful for examples and tests where state should be explicit.

## Console

Console provides a small console-print operation.

~~~python
from pycontinuum import Console

request = Console.print("hello")
~~~

## Why handlers?

Without an effect boundary, business code tends to import concrete database clients, HTTP clients, queues, and SDKs directly.

Handlers keep those choices at the infrastructure boundary. Tests can then provide small in-memory implementations.

## Replay safety

This is the key rule when combining effects with continuations:

**Keep irreversible side effects behind explicit handlers.**

A continuation may replay captured computation. A payment, database write, or message publish must therefore be idempotent or protected against duplicate execution.

## Suggested project layout

~~~text
myapp/
  domain/
    workflows.py
  effects/
    database.py
    messaging.py
  handlers/
    production.py
    testing.py
  main.py
~~~

Keep domain workflows independent from concrete infrastructure.

## Next

Read [Core Concepts](core-concepts.md) to understand continuation replay, then [Resilience](resilience.md) for failure handling.
