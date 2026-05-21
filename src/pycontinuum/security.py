"""Security: safe serialisation, secret redaction, and runtime type validation."""

from __future__ import annotations

import importlib
import json
from typing import Any, Callable, Dict, List, Set, Tuple, Type, TypeVar, Union, get_type_hints, get_origin, get_args

from .core import Continuation

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Secret type – redacts its value when serialised or logged
# ---------------------------------------------------------------------------
class Secret(Generic[T]):
    """A container for sensitive data that is never exposed in serialised form."""

    __slots__ = ("_value",)

    def __init__(self, value: T) -> None:
        self._value = value

    def get(self) -> T:
        return self._value

    def __repr__(self) -> str:
        return "<redacted>"

    def __str__(self) -> str:
        return "<redacted>"


# ---------------------------------------------------------------------------
# Safe serialisation format (JSON‑based)
# ---------------------------------------------------------------------------
def dumps(cont: Continuation) -> bytes:
    """Serialize a continuation to a safe JSON string (no pickle)."""
    data = _continuation_to_dict(cont)
    return json.dumps(data, default=_json_serializer).encode("utf-8")

def loads(blob: bytes, allowed_modules: Set[str] | None = None) -> Continuation:
    """Deserialize a continuation from its JSON representation.

    Only functions from `allowed_modules` (if given) are permitted.
    Raises ValueError on disallowed or missing modules.
    """
    data = json.loads(blob.decode("utf-8"))
    return _dict_to_continuation(data, allowed_modules=allowed_modules)


def _continuation_to_dict(cont: Continuation) -> Dict[str, Any]:
    func = cont._func
    module = func.__module__
    qualname = func.__qualname__
    # Redact secret arguments
    safe_args = tuple(_redact_value(a) for a in cont._args)
    safe_kwargs = {k: _redact_value(v) for k, v in cont._kwargs.items()}
    safe_history = tuple(_redact_value(h) for h in cont._history)
    return {
        "module": module,
        "qualname": qualname,
        "args": safe_args,
        "kwargs": safe_kwargs,
        "history": safe_history,
    }

def _redact_value(value: Any) -> Any:
    if isinstance(value, Secret):
        return {"__secret__": True}
    # For other non‑json types, raise or convert
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)  # fallback, but ideally args should be JSON‑friendly


def _dict_to_continuation(data: Dict[str, Any], allowed_modules: Set[str] | None = None) -> Continuation:
    module = data["module"]
    if allowed_modules is not None and module not in allowed_modules:
        raise ValueError(f"Module '{module}' is not in the allowed list: {allowed_modules}")

    try:
        mod = importlib.import_module(module)
        func = getattr(mod, data["qualname"])
    except (ImportError, AttributeError) as exc:
        raise ValueError(f"Cannot load function {data['qualname']} from {module}: {exc}")

    # Reconstruct args – note that secrets remain as markers; actual secrets must be re‑injected
    args = tuple(data["args"])
    kwargs = dict(data["kwargs"])
    history = tuple(data["history"])

    # Runtime type validation can be added here if type hints stored
    return Continuation(func, args, kwargs, history)


def _json_serializer(obj: Any) -> Any:
    if isinstance(obj, Secret):
        return {"__secret__": True}
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


# ---------------------------------------------------------------------------
# Runtime type validation for continuation inputs
# ---------------------------------------------------------------------------
def validate_continuation_input(cont: Continuation, value: Any) -> None:
    """
    Check that `value` matches the expected input type `A` of the continuation.

    Relies on `cont._type_a` being set (if available). If not, validation is skipped.
    """
    expected_type = getattr(cont, "_type_a", None)
    if expected_type is None:
        # Try to infer from function annotations
        hints = get_type_hints(cont._func)
        # The function is an async generator; its first argument after `self`? Not trivial.
        # So we just skip.
        return

    if not _is_instance(value, expected_type):
        raise TypeError(f"Continuation expects type {expected_type}, but got {type(value).__name__}")

def validate_continuation_result(cont: Continuation, result: Any) -> None:
    """Check that `result` matches the expected output type `B` of the continuation."""
    expected_type = getattr(cont, "_type_b", None)
    if expected_type is None:
        return
    if not _is_instance(result, expected_type):
        raise TypeError(f"Continuation expects output type {expected_type}, but got {type(result).__name__}")


def _is_instance(value: Any, tp: Type) -> bool:
    """Robust isinstance that handles generic types like list[int]."""
    origin = get_origin(tp)
    if origin is not None:
        args = get_args(tp)
        if not isinstance(value, origin):
            return False
        # For simple generics like list[int], check elements recursively
        if origin is list or origin is tuple:
            if not all(_is_instance(x, args[0]) for x in value):
                return False
        elif origin is dict:
            for k, v in value.items():
                if not _is_instance(k, args[0]) or not _is_instance(v, args[1]):
                    return False
        # More complex generics can be added
        return True
    # Plain type
    return isinstance(value, tp)


# ---------------------------------------------------------------------------
# Redaction filter for logging
# ---------------------------------------------------------------------------
class SecretRedactor(logging.Filter):
    """A logging filter that replaces Secret values with '[REDACTED]'."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.args:
            record.args = tuple(_redact_value(a) for a in record.args)
        return True
