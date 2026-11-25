"""`ce publisher project` commands."""

from __future__ import annotations

import click

from ce.publisher.project.abandon import main as abandon_command
from ce.publisher.project.add import main as add_command
from ce.publisher.project.audit import main as audit_group
from ce.publisher.project.complete import main as complete_command
from ce.publisher.project.create import main as create_command
from ce.publisher.project.list import main as list_command
from ce.publisher.project.status import main as status_group
from ce.publisher.project.validation import main as validation_group


@click.group("project")
def main() -> None:
    """Create a project, add files, validate them and publish."""


main.add_command(create_command, name="create")
main.add_command(list_command, name="list")
main.add_command(add_command, name="add")
main.add_command(validation_group, name="validation")
main.add_command(status_group, name="status")
main.add_command(audit_group, name="audit")
main.add_command(complete_command, name="complete")
main.add_command(abandon_command, name="abandon")
