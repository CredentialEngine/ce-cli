"""Token management, refresh, expiry checks."""

from __future__ import annotations

import time
from typing import Optional

_REFRESH_BUFFER = 60  # refresh if token expires 


def get_valid_access_token() -> Optional[str]:
    """Return a valid access token, refreshing silently if needed."""
    from ce.config.settings import load_tokens, save_tokens
    from ce.config.context import get_current_environment
    from ce.auth.device_flow import KeycloakDeviceFlowClient

    tokens = load_tokens()
    if tokens is None:
        return None

    if tokens.expires_at and time.time() < tokens.expires_at - _REFRESH_BUFFER:
        return tokens.access_token

    if tokens.refresh_token:
        result = get_current_environment()
        if result is None:
            return None
        _, env = result
        client = KeycloakDeviceFlowClient(env)
        try:
            tr = client.refresh_access_token(tokens.refresh_token)
            new_tokens = KeycloakDeviceFlowClient.to_stored_tokens(tr)
            save_tokens(new_tokens)
            return new_tokens.access_token
        except Exception:
            return None

    return None


def is_logged_in() -> bool:
    return get_valid_access_token() is not None


def require_login() -> str:
    import click
    token = get_valid_access_token()
    if not token:
        raise click.UsageError(
            "You are not logged in. Run 'ce login' to authenticate."
        )
    return token