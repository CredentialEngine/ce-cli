"""ce publisher project list"""

from __future__ import annotations

import click

from ce.implementations.publisher.cli import (
    console,
    publisher_client,
    publisher_url_option,
)
from ce.implementations.publisher.client import project_kind_label


@click.command("list")
@publisher_url_option
def main(publisher_url: str | None) -> None:
    """List the projects you can see, newest first."""
    with publisher_client(publisher_url) as client:
        projects = client.list_projects()

    for project in sorted(
        projects, key=lambda item: int(item.get("projectId", 0)), reverse=True
    ):
        kind = project_kind_label(project.get("projectType"))
        console.print(
            f"{project.get('projectId'):>6}  {kind:<19} {project.get('status', ''):<10} "
            f"{project.get('publishStatus', ''):<13} {project.get('name', '')}",
            highlight=False,
            soft_wrap=True,
        )
