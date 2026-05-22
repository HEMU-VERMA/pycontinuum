"""Production observability: OpenTelemetry tracing, Prometheus metrics, structured logging.

All instrumentation is optional and gracefully degrades when dependencies are missing.
"""

from __future__ import annotations

import contextvars
import functools
import logging
import time
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Optional imports – if not present, instrumentation becomes a no-op
# ---------------------------------------------------------------------------
try:
    from opentelemetry import trace
    from opentelemetry.trace import SpanKind, Status, StatusCode
    _TRACING_AVAILABLE = True
except ImportError:
    _TRACING_AVAILABLE = False

try:
    from prometheus_client import Counter, Histogram
    _METRICS_AVAILABLE = True
except ImportError:
    _METRICS_AVAILABLE = False

try:
    import structlog
    _STRUCTLOG_AVAILABLE = True
except ImportError:
    _STRUCTLOG_AVAILABLE = False


# ---------------------------------------------------------------------------
# Tracer setup
# ---------------------------------------------------------------------------
_tracer = None
_meter = None

def _get_tracer() -> Any:
    global _tracer
    if _tracer is None and _TRACING_AVAILABLE:
        _tracer = trace.get_tracer("pycontinuum")
    return _tracer

def _get_meter() -> Any:
    """Returns a no-op meter if Prometheus not available."""
    if not _METRICS_AVAILABLE:
        return None
    global _meter
    if _meter is None:
        # We only need Counter and Histogram; CollectorRegistry not used
        _meter = type("Meter", (), {
            "continuation_resumes": Counter(
                "pycontinuum_continuation_resumes_total",
                "Number of times continuations were resumed",
                ["status"]
            ),
            "effect_calls": Counter(
                "pycontinuum_effect_calls_total",
                "Number of effect calls",
                ["effect", "method"]
            ),
            "branch_exploration": Counter(
                "pycontinuum_branch_exploration_total",
                "Branches explored (amb calls)",
                []
            ),
            "continuation_duration": Histogram(
                "pycontinuum_continuation_duration_seconds",
                "Duration of continuation block execution",
                ["type"]
            ),
        })()
    return _meter


# ---------------------------------------------------------------------------
# Context propagation – trace IDs across continuations
# ---------------------------------------------------------------------------
_trace_context = contextvars.ContextVar[Optional[Dict[str, Any]]](
    "pycontinuum_trace", default=None
)

def _capture_trace_context() -> Dict[str, Any] | None:
    if _TRACING_AVAILABLE:
        span = trace.get_current_span()
        if span.is_recording():
            ctx = span.get_span_context()
            return {"trace_id": ctx.trace_id, "span_id": ctx.span_id, "trace_flags": ctx.trace_flags}
    return None

def _restore_trace_context(ctx: Dict[str, Any] | None) -> Any:
    if not ctx or not _TRACING_AVAILABLE:
        return None
    from opentelemetry.trace import SpanContext, TraceFlags
    return SpanContext(
        trace_id=ctx["trace_id"],
        span_id=ctx["span_id"],
        trace_flags=TraceFlags(ctx["trace_flags"]),
        is_remote=True,
    )


# ---------------------------------------------------------------------------
# Structured logging adapter
# ---------------------------------------------------------------------------
class Logger:
    """Thin wrapper around structlog (or plain logging)."""
    def __init__(self) -> None:
        if _STRUCTLOG_AVAILABLE:
            self._logger = structlog.get_logger()
        else:
            self._logger = logging.getLogger("pycontinuum")

    def info(self, event: str, **kwargs: Any) -> None:
        if _STRUCTLOG_AVAILABLE:
            self._logger.info(event, **kwargs)
        else:
            self._logger.info(f"{event} {kwargs}")

    def error(self, event: str, **kwargs: Any) -> None:
        if _STRUCTLOG_AVAILABLE:
            self._logger.error(event, **kwargs)
        else:
            self._logger.error(f"{event} {kwargs}")

    def debug(self, event: str, **kwargs: Any) -> None:
        if _STRUCTLOG_AVAILABLE:
            self._logger.debug(event, **kwargs)
        else:
            self._logger.debug(f"{event} {kwargs}")


_logger = Logger()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def instrument(service_name: str = "pycontinuum") -> None:
    """Activate instrumentation for the current process.
    This must be called before any effectful code.
    """
    _patch_continuation_call()
    _patch_reset()
    if _METRICS_AVAILABLE:
        _get_meter()
        _logger.info("PyContinuum metrics registered")


def _patch_continuation_call() -> None:
    from .core import Continuation
    original_call = Continuation.__call__

    @functools.wraps(original_call)
    async def traced_call(self, value):
        tracer = _get_tracer()
        span_name = "continuation.resume"
        attributes = {"pycontinuum.value": str(value)}
        parent = _restore_trace_context(_trace_context.get())

        exc: Optional[BaseException] = None
        start = time.monotonic()
        try:
            if tracer:
                with tracer.start_as_current_span(
                    span_name,
                    kind=SpanKind.INTERNAL,
                    attributes=attributes,
                    links=[parent] if parent else None,
                ) as span:
                    result = await original_call(self, value)
                    span.set_status(Status(StatusCode.OK))
                    return result
            else:
                return await original_call(self, value)
        except BaseException as e:
            exc = e
            if tracer:
                span = trace.get_current_span()
                span.set_status(Status(StatusCode.ERROR, str(e)))
            raise
        finally:
            duration = time.monotonic() - start
            meter = _get_meter()
            if meter:
                meter.continuation_resumes.labels(
                    status="error" if exc else "success"
                ).inc()
                meter.continuation_duration.labels("continuation").observe(duration)

    Continuation.__call__ = traced_call


def _patch_reset() -> None:
    from . import core
    original_reset = core.reset

    @functools.wraps(original_reset)
    async def traced_reset(coro_func, *args, **kwargs):
        tracer = _get_tracer()
        span_name = f"reset {coro_func.__name__}" if hasattr(coro_func, "__name__") else "reset"
        if tracer:
            with tracer.start_as_current_span(span_name, kind=SpanKind.INTERNAL) as span:
                token = _trace_context.set(_capture_trace_context())
                try:
                    result = await original_reset(coro_func, *args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except BaseException as exc:
                    span.set_status(Status(StatusCode.ERROR, str(exc)))
                    raise
                finally:
                    _trace_context.reset(token)
        else:
            return await original_reset(coro_func, *args, **kwargs)

    core.reset = traced_reset


def record_effect_call(effect_name: str, method: str, duration: float) -> None:
    """Record an effect call metric."""
    meter = _get_meter()
    if meter:
        meter.effect_calls.labels(effect=effect_name, method=method).inc()
    _logger.debug("Effect call", effect=effect_name, method=method, duration=duration)
