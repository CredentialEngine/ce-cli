"""ce publisher project abandon"""

from __future__ import annotations

import click

from ce.implementations.publisher.cli import (
    console,
    project_option,
    publisher_client,
    publisher_url_option,
)


@click.command("abandon")
@project_option
@click.option("--yes", "-y", is_flag=True, help="Skip the confirmation prompt.")
@publisher_url_option
def main(project_id: int, yes: bool, publisher_url: str | None) -> None:
    """Abandon a project that has not been published."""
    if not yes:
        click.confirm(f"  Abandon project {project_id}?", abort=True)

    with publisher_client(publisher_url) as client:
        client.abandon(project_id)

    console.print(f"Project {project_id} is abandoned.", highlight=False)
