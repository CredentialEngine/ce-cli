"""Credential Engine CLI - main entry point."""

try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

import click
from rich.console import Console

from ce import __version__
from ce.commands.auth import account_show, login, logout
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
      ce env list                      Select your environment (dev / sandbox / prod)
      ce login                         Sign in via Keycloak device authorization
      ce whoami                        Confirm who you are signed in as

    \b
    Everyday use:
      ce logout                        Sign out
      ce env use <name>                Switch environment

    \b
    Run any command with --help for full options:
      ce login --help
      ce iir challenge bulk-sign --help
    """
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug

    if debug:
        from ce.utils.logging import enable_debug
        enable_debug()


# Top-level account commands (promoted from `ce account ...`)
cli.add_command(login, name="login")           # ce login
cli.add_command(logout, name="logout")         # ce logout
cli.add_command(account_show, name="whoami")   # ce whoami

# Command groups
cli.add_command(env_group)        # ce env list / use / show
cli.add_command(iir_group)        # ce iir challenge ... / ce iir issuer-did ...
cli.add_command(version_command)  # ce version