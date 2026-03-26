
from __future__ import annotations

import os
import sys
import time
from typing import Any

from rich.console import Console
from rich.text import Text

_stderr = Console(stderr=True)

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
        "debug":   ("[dim blue]DEBUG[/dim blue]",   False),
        "info":    ("[dim green]INFO [/dim green]",  False),
        "warning": ("[yellow]WARN [/yellow]",        False),  
        "error":   ("[red]ERROR[/red]",              True),   # always shown
    }

    def __init__(self, name: str) -> None:
        self._name = name.split(".")[-1]  

    def _emit(self, level: str, message: str, **fields: Any) -> None:
        label, always = self._LEVELS[level]
        if not always and not _debug_enabled:
            return

        parts = [label, f"[dim]{self._name}[/dim]", message]
        if fields:
            kv = "  ".join(f"[dim]{k}[/dim]=[cyan]{v}[/cyan]" for k, v in fields.items())
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
        self.debug(f"→ {method} {url}", **extra)
        return time.monotonic()

    def http_response(self, status: int, start: float, **extra: Any) -> None:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        colour = "green" if status < 400 else "red"
        self.debug(f"← [{colour}]{status}[/{colour}] ({elapsed_ms}ms)", **extra)


def get_logger(name: str) -> CELogger:
    """Return a :class:`CELogger` for the given module name."""
    return CELogger(name)
