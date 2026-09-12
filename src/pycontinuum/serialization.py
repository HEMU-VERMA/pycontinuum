"""Serialization utilities for continuations."""

import pickle
from typing import Any, cast

from .core import Continuation


def dumps(cont: Continuation[Any, Any]) -> bytes:
    """Serialize a continuation using pickle."""
    return pickle.dumps(cont)


def loads(data: bytes) -> Continuation[Any, Any]:
    """Deserialize a continuation previously created by :func:`dumps`."""
    value = pickle.loads(data)
    return cast(Continuation[Any, Any], value)
