"""Credential Engine CLI - main entry point."""

try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

import click
from rich.console import Console

from ce import __version__
from ce.commands.auth import auth_group
from ce.commands.env import env_group
from ce.commands.iir import iir_group
from ce.commands.version import version_command

console = Console()

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__version__, prog_name="ce")
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    envvar="CE_DEBUG",
    help="Enable debug output (HTTP traces, token refresh events, etc.).",
)
@click.pass_context
def cli(ctx: click.Context, debug: bool) -> None:
    """Credential Engine CLI.

    Manage Credential Engine platform resources and services.

    \b
    First time?
      ce env list              Select your environment (dev / sandbox / prod)
      ce login                 Sign in via Keycloak device authorization
      ce whoami                Confirm who you are signed in as

    \b
    Everyday use:
      ce logout                Sign out
      ce env use <n>           Switch environment

    \b
    IIR — bulk DID upload:
      ce iir bulk-upload-dids sign-challenges --csv input.csv
      ce iir bulk-upload-dids publish   --output-file Output-input-....csv

    \b
    Run any command with --help for full options:
      ce login --help
      ce iir bulk-upload-dids sign-challenges --help
    """
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug

    if debug:
        from ce.utils.logging import enable_debug
        enable_debug()


# Top-level commands

@cli.command("login")
@click.option("--env", "env_name", default=None, metavar="NAME",
              help="Environment to log in to (default: active environment).")
@click.pass_context
def login_alias(ctx: click.Context, env_name: str | None) -> None:
    """Sign in to Credential Engine via Keycloak device authorization."""
    from ce.commands.auth import login as _login
    ctx.invoke(_login, env_name=env_name)


@cli.command("logout")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt.")
@click.pass_context
def logout_alias(ctx: click.Context, yes: bool) -> None:
    """Sign out and remove stored credentials."""
    from ce.commands.auth import logout as _logout
    ctx.invoke(_logout, yes=yes)


@cli.command("whoami")
@click.pass_context
def whoami(ctx: click.Context) -> None:
    """Show the currently signed-in account."""
    from ce.commands.auth import account_show as _show
    ctx.invoke(_show)


# Command groups

cli.add_command(auth_group)     # ce account ...
cli.add_command(env_group)      # ce env ...
cli.add_command(iir_group)      # ce iir ...
cli.add_command(version_command)  # ce version