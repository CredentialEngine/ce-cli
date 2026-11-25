
from __future__ import annotations

import os
import time
from typing import Any

from ce.utils.display import new_console

_stderr = new_console(stderr=True)

_debug_enabled: bool = bool(os.environ.get("CE_DEBUG", ""))


def enable_debug() -> None:
    """Turn on debug output for the duration of the process."""
    global _debug_enabled
    _debug_enabled = True


def is_debug() -> bool:
    return _debug_enabled


class CELogger:
    """Lightweight structured logger that writes to stderr via Rich."""

    _LEVELS = {
        "debug":   ("DEBUG", False),
        "info":    ("INFO ", False),
        "warning": ("WARN ", False),
        "error":   ("ERROR", True),   # always shown
    }

    def __init__(self, name: str) -> None:
        self._name = name.split(".")[-1]  

    def _emit(self, level: str, message: str, **fields: Any) -> None:
        label, always = self._LEVELS[level]
        if not always and not _debug_enabled:
            return

        parts = [label, self._name, message]
        if fields:
            kv = "  ".join(f"{k}={v}" for k, v in fields.items())
            parts.append(kv)

        _stderr.print("  ".join(parts))

    def debug(self, message: str, **fields: Any) -> None:
        self._emit("debug", message, **fields)

    def info(self, message: str, **fields: Any) -> None:
        self._emit("info", message, **fields)

    def warning(self, message: str, **fields: Any) -> None:
        self._emit("warning", message, **fields)

    def error(self, message: str, **fields: Any) -> None:
        self._emit("error", message, **fields)


    def http_request(self, method: str, url: str, **extra: Any) -> float:
        """Log an outgoing HTTP request; returns start time for latency tracking."""
        self.debug(f"-> {method} {url}", **extra)
        return time.monotonic()

    def http_response(self, status: int, start: float, **extra: Any) -> None:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        self.debug(f"<- {status} ({elapsed_ms}ms)", **extra)


def get_logger(name: str) -> CELogger:
    """Return a :class:`CELogger` for the given module name."""
    return CELogger(name)
