"""Auth commands: ce login, ce logout, ce whoami."""

from __future__ import annotations

import click

from ce.auth.device_flow import (
    AccessDeniedError,
    DeviceFlowError,
    KeycloakDeviceFlowClient,
    TokenExpiredError,
)
from ce.auth.token_manager import (
    UNREACHABLE,
    is_logged_in,
    login_required_message,
    resolve_access_token,
)
from ce.config.context import get_current_environment, load_cli_config
from ce.config.settings import delete_tokens, load_tokens, save_tokens
from ce.utils.display import new_console, print_pairs

console = new_console()
err_console = new_console(stderr=True)


@click.group("account")
def auth_group() -> None:
    """Manage Credential Engine account and authentication."""


# ce login

@click.command("login")
@click.option("--env", "env_name", default=None, metavar="NAME",
              help="Environment to log in to (default: active environment).")
def login(env_name: str | None) -> None:
    """Sign in to Credential Engine via Keycloak device authorization.

    Uses the active environment's device_auth_url, token_url, and client_id.
    Override with --env to target a specific environment.
    """
    config = load_cli_config()

    if env_name:
        if env_name not in config.environments:
            err_console.print(f"Unknown environment {env_name}. "
                              f"Run ce env list to see available environments.")
            raise SystemExit(1)
        env = config.environments[env_name]
        active_name = env_name
    else:
        result = get_current_environment()
        if result is None:
            err_console.print("No active environment. Run ce env use <name> first.")
            raise SystemExit(1)
        active_name, env = result

    # Reuse this environment's session rather than starting a second sign-in.
    # An expired access token is renewed here; if it cannot be, sign-in goes ahead.
    if is_logged_in(active_name):
        console.print(f"Already signed in to {active_name} "
                      f"({env.label}). Run ce account show for details.")
        console.print("  To switch accounts, run ce account logout first.")
        return

    client = KeycloakDeviceFlowClient(env)

    console.print()
    with console.status(f"Contacting {env.label} Keycloak..."):
        try:
            device_auth = client.request_device_code()
        except DeviceFlowError as exc:
            err_console.print(f"Error: {exc}")
            raise SystemExit(1)

    console.print(f"Sign in to Credential Engine: {active_name} ({env.label})")
    console.print()
    console.print("Open a browser and go to:")
    console.print(f"  {device_auth.verification_uri}")
    console.print("Then enter the code:")
    console.print(f"  {device_auth.user_code}")
    if device_auth.verification_uri_complete:
        console.print("Or open the direct link:")
        console.print(f"  {device_auth.verification_uri_complete}")
    console.print()

    try:
        with console.status("Waiting for you to approve in the browser...", spinner="dots"):
            token_resp = client.poll_for_token(
                device_code=device_auth.device_code,
                interval=device_auth.interval,
                expires_in=device_auth.expires_in,
            )
    except AccessDeniedError:
        console.print()
        err_console.print("Authorization was denied.")
        raise SystemExit(1)
    except TokenExpiredError:
        console.print()
        err_console.print("The device code expired. Run ce login again.")
        raise SystemExit(1)
    except DeviceFlowError as exc:
        console.print()
        err_console.print(f"Error: {exc}")
        raise SystemExit(1)

    stored = KeycloakDeviceFlowClient.to_stored_tokens(token_resp)
    save_tokens(stored, active_name)

    try:
        userinfo = client.get_userinfo(stored.access_token)
        name = userinfo.get("name") or userinfo.get("preferred_username") or "there"
        email = userinfo.get("email", "")
    except Exception:
        name, email = "there", ""

    console.print()
    greeting = f"Signed in as {name}"
    if email:
        greeting += f" ({email})"
    greeting += f"  -> {active_name} ({env.label})"
    console.print(greeting)
    console.print("  Run ce whoami to view your account details.")
    console.print()


# ce account logout

@click.command("logout")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt.")
def logout(yes: bool) -> None:
    """Sign out and remove stored credentials."""
    tokens = load_tokens()
    if tokens is None:
        console.print("You are not currently signed in.")
        return

    if not yes:
        click.confirm("  Sign out of Credential Engine?", abort=True)

    result = get_current_environment()
    if result and tokens.refresh_token:
        _, env = result
        try:
            KeycloakDeviceFlowClient(env).revoke_token(tokens.refresh_token, "refresh_token")
        except DeviceFlowError as exc:
            err_console.print(
                f"Warning: the session could not be ended at the sign-in service: {exc}",
                highlight=False,
                soft_wrap=True,
            )

    delete_tokens()
    console.print("Signed out successfully.")


# ce account show

@click.command("show")
def account_show() -> None:
    """Show the currently signed-in account."""
    tokens = load_tokens()
    if tokens is None:
        console.print("Not signed in. Run ce login.")
        return

    result = get_current_environment()
    if result is None:
        err_console.print("No active environment.")
        return
    active_name, env = result

    session = resolve_access_token()
    token = session.access_token
    if not token:
        err_console.print(login_required_message(session), highlight=False, soft_wrap=True)
        if session.reason == UNREACHABLE:
            raise SystemExit(1)
        return

    # The token may just have been renewed; show the saved one's expiry.
    tokens = load_tokens() or tokens

    client = KeycloakDeviceFlowClient(env)
    try:
        userinfo = client.get_userinfo(token)
    except Exception as exc:
        err_console.print(f"Error fetching account info: {exc}")
        return

    rows = [
        ("Environment", f"{active_name} ({env.label})"),
        ("API endpoint base", env.publisher_base),
        ("Name", userinfo.get("name", "-")),
        ("Username", userinfo.get("preferred_username", "-")),
        ("Email", userinfo.get("email", "-")),
        ("UserId", userinfo.get("sub", "-")),
    ]
    if tokens.scope:
        rows.append(("Scopes", tokens.scope))
    if tokens.expires_at:
        import datetime
        exp = datetime.datetime.fromtimestamp(tokens.expires_at).strftime("%Y-%m-%d %H:%M:%S")
        rows.append(("Token expires", exp))

    console.print()
    print_pairs(console, rows)
    console.print()


auth_group.add_command(login)
auth_group.add_command(logout)
auth_group.add_command(account_show)