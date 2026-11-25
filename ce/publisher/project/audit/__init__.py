"""`ce publisher project audit` commands."""

from __future__ import annotations

import click

from ce.publisher.project.audit.show import main as show_command


@click.group("audit")
def main() -> None:
    """The log of what was done to a project."""


main.add_command(show_command, name="show")
