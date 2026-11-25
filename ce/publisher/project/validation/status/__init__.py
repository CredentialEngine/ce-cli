"""`ce publisher project validation status` commands."""

from __future__ import annotations

import click

from ce.publisher.project.validation.status.show import main as show_command


@click.group("status")
def main() -> None:
    """How many files passed validation, for the project's latest iteration."""


main.add_command(show_command, name="show")
