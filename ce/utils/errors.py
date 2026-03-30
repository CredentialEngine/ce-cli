"""Shared decorators and error-handling utilities for CE commands."""

from __future__ import annotations

import functools
import sys
from typing import Callable

import click
from rich.console import Console

from ce.utils.http import APIError

err_console = Console(stderr=True)


def handle_api_errors(f: Callable) -> Callable:
    """Decorator: catch APIError / httpx errors and print a friendly message."""

    @functools.wraps(f)
    def wrapper(*args, **kwargs): 
        try:
            return f(*args, **kwargs)
        except APIError as exc:
            if exc.status_code == 401:
                err_console.print(
                    "[red]✗[/red] Unauthorized. Your session may have expired — run [bold]ce login[/bold]."
                )
            elif exc.status_code == 403:
                err_console.print(
                    f"[red]✗[/red] Permission denied: {exc.message}"
                )
            elif exc.status_code == 404:
                err_console.print(
                    f"[red]✗[/red] Not found: {exc.message}"
                )
            else:
                err_console.print(f"[red]✗[/red] API error: {exc.message}")
            sys.exit(1)
        except click.UsageError:
            raise   
        except Exception as exc:
            err_console.print(f"[red]✗[/red] Unexpected error: {exc}")
            sys.exit(1)

    return wrapper
