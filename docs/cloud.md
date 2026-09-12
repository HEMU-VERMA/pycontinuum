# Cloud Runtime

PyContinuum is designed so continuation-based business workflows can be separated from their infrastructure.

## Persisting workflows

A captured continuation can be represented as application data. When building a distributed worker system, store that data in your chosen durable store and resume it in a controlled worker process.

## Safety

Serialized continuation data must be treated as trusted application input only after validation. Restrict allowed modules and types when restoring state, and never deserialize untrusted data blindly.

## Deployment architecture

A practical deployment can use:

```text
API / Worker
    |
    v
PyContinuum workflow
    |
    +--> effect handlers --> database / APIs / queues
    |
    +--> durable workflow state
```

Keep cloud-specific adapters outside the core package so users can choose their queue, database, tracing system, and deployment platform.

## Observability

Use application logging and tracing around workflow boundaries. Record correlation IDs and terminal outcomes, not secrets or raw serialized credentials.
