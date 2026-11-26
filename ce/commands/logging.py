"""Persistent logging preferences."""

import click

from ce.config.context import load_cli_config, save_cli_config
from ce.utils.cli_logging import LogLevelChoice
from ce.utils.logging import DEFAULT_LOG_LEVEL, set_logging_level


@click.group("logging")
def logging_group():
    """Inspect or change CLI logging preferences."""


@logging_group.command("show")
def show():
    """Show the current logging level."""
    click.echo(load_cli_config().log_level or DEFAULT_LOG_LEVEL)


@logging_group.group("set")
def set_group():
    """Set logging preferences."""


@set_group.command("log-level")
@click.argument("level", type=LogLevelChoice())
def set_level(level):
    """Set the logging threshold for subsequent commands."""
    config = load_cli_config()
    config.log_level = level.upper()
    save_cli_config(config)
    set_logging_level(config.log_level)
    click.echo(config.log_level)
