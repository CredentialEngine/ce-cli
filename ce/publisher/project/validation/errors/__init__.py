"""`ce publisher project validation errors` commands."""

from __future__ import annotations

import click

from ce.publisher.project.validation.errors.show import main as show_command


@click.group("errors")
def main() -> None:
    """The validation errors of the project's latest iteration."""


main.add_command(show_command, name="show")
