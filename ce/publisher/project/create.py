"""ce publisher project create"""

from __future__ import annotations

import click

from ce.implementations.publisher.cli import console, fail, publisher_client, publisher_url_option


@click.command("create")
@click.option("--name", required=True, help="A name to recognise the project by.")
@click.option("--jsonld", is_flag=True,
              help="Create an API publishing project (JSON-LD files only) instead of a BU project.")
@publisher_url_option
def main(name: str, jsonld: bool, publisher_url: str | None) -> None:
    """Create a project: a BU project takes BU template CSVs, an API publishing project takes JSON-LD."""
    if not name.strip():
        fail("The project needs a name.")

    with publisher_client(publisher_url) as client:
        project_id = client.create_project(name.strip(), jsonld=jsonld)

    console.print(f"Created project {project_id}", highlight=False)
