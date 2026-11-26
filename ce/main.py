"""Credential Engine CLI - main entry point."""

try:
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass

import click

from ce import __version__
from ce.commands.auth import account_show, login, logout
from ce.commands.env import env_group
from ce.commands.iir import iir_group
from ce.commands.logging import logging_group
from ce.commands.registry import registry_group
from ce.commands.version import version_command
from ce.config.context import load_cli_config
from ce.publisher import main as publisher_group
from ce.utils.cli_logging import VersionedGroup
from ce.utils.logging import DEFAULT_LOG_LEVEL, configure_logging

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group(cls=VersionedGroup, context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__version__, prog_name="ce")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Credential Engine CLI.

    Manage Credential Engine platform resources and services.

    \b
    First time?
      ce env list                      List available environments
      ce env use <name>                Select your environment
      ce login                         Sign in via Keycloak device authorization
      ce whoami                        Confirm who you are signed in as

    \b
    Everyday use:
      ce logout                        Sign out
      ce env use <name>                Switch environment
      ce publisher project create      Publish CSVs or JSON-LD to the Credential Registry, step by step

    \b
    Run any command with --help for full options:
      ce login --help
      ce iir challenge bulk-sign --help
    """
    ctx.ensure_object(dict)
    level = load_cli_config().log_level or DEFAULT_LOG_LEVEL
    ctx.obj["debug"] = level == "DEBUG"
    try:
        configure_logging(log_level=level)
    except (ValueError, ImportError) as exc:
        raise click.ClickException(str(exc)) from exc


# Top-level account commands (promoted from `ce account ...`)
cli.add_command(login, name="login")  # ce login
cli.add_command(logout, name="logout")  # ce logout
cli.add_command(account_show, name="whoami")  # ce whoami

# Command groups
cli.add_command(env_group)  # ce env list / use / show
cli.add_command(iir_group)  # ce iir challenge ... / ce iir issuer-did ...
cli.add_command(publisher_group)  # ce publisher project ...
cli.add_command(version_command)  # ce version
cli.add_command(registry_group)
cli.add_command(logging_group)
