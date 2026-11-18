"""Shared decorators and error-handling utilities for CE commands."""

from __future__ import annotations

import functools
import sys
from typing import Callable

import click

from ce.utils.display import new_console
from ce.utils.http import APIError

err_console = new_console(stderr=True)


def handle_api_errors(f: Callable) -> Callable:
    """Decorator: catch APIError / httpx2 errors and print a friendly message."""

    @functools.wraps(f)
    def wrapper(*args, **kwargs): 
        try:
            return f(*args, **kwargs)
        except APIError as exc:
            if exc.status_code == 401:
                err_console.print(
                    "Error: Unauthorized. Your session may have expired — run ce login."
                )
            elif exc.status_code == 403:
                err_console.print(
                    f"Error: Permission denied: {exc.message}"
                )
            elif exc.status_code == 404:
                err_console.print(
                    f"Error: Not found: {exc.message}"
                )
            else:
                err_console.print(f"API error: {exc.message}")
            sys.exit(1)
        except click.UsageError:
            raise   
        except Exception as exc:
            err_console.print(f"Unexpected error: {exc}")
            sys.exit(1)

    return wrapper
