"""Serialization utilities for continuations."""
import pickle
from .core import Continuation

def dumps(cont: Continuation) -> bytes:
    return pickle.dumps(cont)

def loads(data: bytes) -> Continuation:
    return pickle.loads(data)