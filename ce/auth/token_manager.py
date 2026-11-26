"""Token management, refresh, expiry checks."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

_REFRESH_BUFFER = 60  # refresh if token expires within this many seconds

NOT_LOGGED_IN = "not_logged_in"
SESSION_EXPIRED = "session_expired"
UNREACHABLE = "unreachable"
CLIENT_CONFIGURATION = "client_configuration"


@dataclass
class TokenResult:
    """An access token, or why there is none.

    reason is NOT_LOGGED_IN (no saved session), SESSION_EXPIRED (Keycloak
    refused to renew it; the saved session was removed) or UNREACHABLE (the
    sign-in service could not be reached; the saved session is kept).
    """

    access_token: str | None = None
    reason: str | None = None
    detail: str = ""


def resolve_access_token(
    env_name: str | None = None, *, force_refresh: bool = False
) -> TokenResult:
    """Return a valid access token for an environment (the active one by default).

    The token is renewed silently when it is about to expire, or when
    force_refresh is set (after the API answered 401, for example).
    """
    from ce.auth.device_flow import (
        ClientConfigurationError,
        DeviceFlowError,
        KeycloakDeviceFlowClient,
        RefreshRejectedError,
    )
    from ce.config.context import get_current_environment, load_cli_config
    from ce.config.settings import delete_tokens, load_tokens, save_tokens

    if env_name is None:
        current = get_current_environment()
        if current is None:
            return TokenResult(reason=NOT_LOGGED_IN)
        env_name, env = current
    else:
        env = load_cli_config().environments.get(env_name)
        if env is None:
            return TokenResult(reason=NOT_LOGGED_IN)

    tokens = load_tokens(env_name)
    if tokens is None:
        return TokenResult(reason=NOT_LOGGED_IN)

    fresh = tokens.expires_at and time.time() < tokens.expires_at - _REFRESH_BUFFER
    if fresh and not force_refresh and tokens.access_token.strip():
        return TokenResult(access_token=tokens.access_token)

    if not tokens.refresh_token:
        delete_tokens(env_name)
        return TokenResult(reason=SESSION_EXPIRED)

    logging.getLogger(__name__).debug("Refreshing saved access token for %s", env_name)
    client = KeycloakDeviceFlowClient(env)
    try:
        tr = client.refresh_access_token(tokens.refresh_token)
    except ClientConfigurationError as exc:
        return TokenResult(reason=CLIENT_CONFIGURATION, detail=str(exc))
    except RefreshRejectedError as exc:
        # The session ended at Keycloak; the saved tokens can never work again.
        delete_tokens(env_name)
        return TokenResult(reason=SESSION_EXPIRED, detail=str(exc))
    except DeviceFlowError as exc:
        # A passing failure must not sign the user out.
        return TokenResult(reason=UNREACHABLE, detail=str(exc))

    new_tokens = KeycloakDeviceFlowClient.to_stored_tokens(tr)
    save_tokens(new_tokens, env_name)
    return TokenResult(access_token=new_tokens.access_token)


def get_valid_access_token(
    env_name: str | None = None, *, force_refresh: bool = False
) -> str | None:
    """Return a valid access token, refreshing silently if needed."""
    return resolve_access_token(env_name, force_refresh=force_refresh).access_token


def is_logged_in(env_name: str | None = None) -> bool:
    return get_valid_access_token(env_name) is not None


def login_required_message(result: TokenResult) -> str:
    """What to tell the user when there is no access token."""
    if result.reason == SESSION_EXPIRED:
        return "Your session has expired. Run 'ce login' to sign in again."
    if result.reason == CLIENT_CONFIGURATION:
        return f"{result.detail} Saved session retained."
    if result.reason == UNREACHABLE:
        return f"Could not renew your session ({result.detail}). You are still signed in; try again."
    return "You are not logged in. Run 'ce login' to authenticate."


def require_login() -> str:
    import click

    result = resolve_access_token()
    if not result.access_token:
        if result.reason in (UNREACHABLE, CLIENT_CONFIGURATION):
            raise click.ClickException(login_required_message(result))
        raise click.UsageError(login_required_message(result))
    return result.access_token
