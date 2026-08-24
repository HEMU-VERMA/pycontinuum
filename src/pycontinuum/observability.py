"""Distributed tracing and Prometheus metrics for continuations."""

from __future__ import annotations

import contextvars
import logging
import time
import types
from typing import Any, Self

_trace_context: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "pycontinuum_trace", default=None
)


def current_trace() -> dict[str, Any] | None:
    return _trace_context.get()


def set_trace(trace: dict[str, Any] | None) -> contextvars.Token[dict[str, Any] | None]:
    return _trace_context.set(trace)


class Tracer:
    """Lightweight tracing manager for continuation execution paths."""

    def __init__(self, service_name: str = "pycontinuum") -> None:
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)

    def start_span(self, name: str) -> _SpanContext:
        return _SpanContext(name, self.logger)


class _SpanContext:
    def __init__(self, name: str, logger: logging.Logger) -> None:
        self.name = name
        self.logger = logger
        self.start_time = 0.0

    async def __aenter__(self) -> Self:
        self.start_time = time.monotonic()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> bool:
        duration = time.monotonic() - self.start_time
        self.logger.debug("Span %s completed in %.4fs", self.name, duration)
        return False