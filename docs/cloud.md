# Cloud Runtime

PyContinuum separates continuation-based business workflows from infrastructure.

## Persisting workflows

Represent workflow state as application data and store it in a durable system of your choice. Resume it only in a controlled worker process.

## Safety

Treat serialized continuation data as trusted application input only after validation. Restrict allowed modules and types when restoring state and never deserialize untrusted data blindly.

## Deployment architecture

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

Keep cloud adapters outside the core package so deployments can choose their own storage, queue, tracing, and orchestration systems.
