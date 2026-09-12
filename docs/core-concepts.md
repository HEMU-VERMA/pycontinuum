# Core Concepts

## Continuations

A continuation is the rest of a computation from a particular point onward.

PyContinuum captures that remainder up to the nearest reset boundary and represents it as a Continuation object.

## reset

reset establishes a delimited boundary:

~~~python
result = await reset(workflow)
~~~

Only computation inside that boundary can be captured by shift.

## shift

shift suspends the current computation and passes its continuation to a handler:

~~~python
async def workflow():
    answer = await shift(lambda k: k(42))
    return answer
~~~

Calling k(42) resumes the computation with 42 at the suspension point.

## Multi-shot execution

The same continuation can be resumed more than once:

~~~python
async def workflow():
    answer = await shift(lambda k: [k(10), k(20)])
    return answer
~~~

The captured computation is replayed for each supplied value.

## Exceptions

A continuation can also be resumed by injecting an exception:

~~~python
result = continuation.throw(ValueError("invalid"))
~~~

This is useful when the next execution should handle an error at the captured suspension point.

## abort

abort terminates the current delimited computation with an exception.

~~~python
from pycontinuum import abort

await abort(RuntimeError("workflow stopped"))
~~~

## Why replay?

Python does not expose a safe way to clone an interpreter stack. PyContinuum instead records suspension decisions and replays the function with its recorded history.

This provides multi-shot behavior while keeping application code as ordinary async Python.

## Side effects

Replay means irreversible effects must be isolated.

Safe to replay:
- calculations
- validation
- parsing
- pure domain logic

Protect or isolate:
- database writes
- payments
- message publishing
- external HTTP mutations

Use the effect/handler layer for infrastructure operations.

## When to use continuations

Good fits include constraint solving, backtracking, parser exploration, probabilistic branching, resumable workflows, and structured effect handling.

For ordinary linear async code, normal async/await is simpler.
