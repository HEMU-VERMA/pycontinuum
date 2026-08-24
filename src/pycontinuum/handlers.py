"""Built-in effect handlers."""

from __future__ import annotations

import contextvars
from typing import Any

_current_handler: contextvars.ContextVar[Any | None] = contextvars.ContextVar(
    "current_handler", default=None
)


class StateHandler:
    """Handler for state effects."""

    def __init__(self, initial_state: Any = 0) -> None:
        self.state = initial_state

    @staticmethod
    def get() -> tuple[str]:
        return ("get",)

    @staticmethod
    def put(val: Any) -> tuple[str, Any]:
        return ("put", val)

    def handle(self, req: Any) -> Any:
        if isinstance(req, tuple) and len(req) > 0:
            if req[0] == "get":
                return self.state
            if req[0] == "put" and len(req) > 1:
                self.state = req[1]
                return None
        return None


class Console:
    """Handler for console I/O effects."""

    @staticmethod
    def print(msg: str) -> tuple[str, str]:
        return ("print", msg)

    def handle(self, req: Any) -> Any:
        if isinstance(req, tuple) and len(req) > 1 and req[0] == "print":
            return None
        return None