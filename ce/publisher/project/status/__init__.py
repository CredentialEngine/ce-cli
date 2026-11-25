"""`ce publisher project status` commands."""

from __future__ import annotations

import click

from ce.publisher.project.status.show import main as show_command


@click.group("status")
def main() -> None:
    """The state of a project."""


main.add_command(show_command, name="show")
