"""Shared saved-login authentication for Consumer and Publisher API requests."""

from __future__ import annotations

import click

from ce.auth.token_manager import login_required_message, resolve_access_token


def require_api_token(env_name: str, *, force_refresh: bool = False) -> str:
    result = resolve_access_token(env_name, force_refresh=force_refresh)
    if not result.access_token or not result.access_token.strip():
        raise click.ClickException(login_required_message(result))
    return result.access_token


def rejected_token() -> click.ClickException:
    return click.ClickException(
        "API rejected the renewed token (HTTP 401). Run 'ce login' again; "
        "if this persists, check the token issuer, audience and API permissions."
    )
