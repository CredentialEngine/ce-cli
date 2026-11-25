"""`ce publisher project validation` commands."""

from __future__ import annotations

import click

from ce.publisher.project.validation.errors import main as errors_group
from ce.publisher.project.validation.run import main as run_command
from ce.publisher.project.validation.status import main as status_group


@click.group("validation")
def main() -> None:
    """Run validation on a project and show what it found."""


main.add_command(run_command, name="run")
main.add_command(status_group, name="status")
main.add_command(errors_group, name="errors")
