"""ce publisher project add"""

from __future__ import annotations

from pathlib import Path

import click

from ce.implementations.publisher import service
from ce.implementations.publisher.cli import (
    console,
    fail,
    project_option,
    publisher_client,
    publisher_url_option,
)
from ce.implementations.publisher.client import BULK_UPLOAD_PROJECT, PublisherApiError


@click.command("add")
@project_option
@click.option(
    "--file",
    "paths",
    multiple=True,
    required=True,
    type=click.Path(path_type=Path),
    help="A file, or a folder of them. Repeat for several.",
)
@click.option(
    "--type",
    "template",
    default=None,
    metavar="TEMPLATE",
    help="What the CSV files hold, by BU template: credentials, learning-opportunities, "
    "assessments, ... A command adds files of one template.",
)
@click.option("--recursive", "-r", is_flag=True, help="Include files in subfolders.")
@publisher_url_option
def main(
    project_id: int,
    paths: tuple[Path, ...],
    template: str | None,
    recursive: bool,
    publisher_url: str | None,
) -> None:
    """Add files to a project, or replace the files of the same name.

    \b
    A BU project takes .csv files and starts validating them at once.
    An API publishing project takes .json or .jsonld files; run validation yourself.
    Every add after validation has run starts a new iteration.

    \b
    Examples:
      ce publisher project add --project-id 23 --file credentials.csv --type credentials
      ce publisher project add --project-id 24 --file .\\jsonld\\
    """
    with publisher_client(publisher_url) as client:
        project = client.get_project(project_id)
        kind = project.get("projectType")

        try:
            files = service.collect_files(
                paths, service.extensions_for(kind), recursive=recursive
            )
            if kind == BULK_UPLOAD_PROJECT:
                resource_class = service.resolve_resource_class(template)
            elif template:
                raise PublisherApiError(
                    "--type applies to CSV files; an API publishing project does not take it."
                )
        except PublisherApiError as exc:
            fail(str(exc))

        if kind == BULK_UPLOAD_PROJECT:
            result = client.upload_csv(project_id, files, resource_class)
        else:
            result = client.upload_jsonld(project_id, files)

    for path in files:
        console.print(f"Added {path.name}", highlight=False, soft_wrap=True)

    note = (
        " Validation has started."
        if kind == BULK_UPLOAD_PROJECT
        else " Run validation when you have added everything."
    )
    console.print(
        f"{len(files)} file(s) in iteration {result.get('iterationId')}.{note}",
        highlight=False,
        soft_wrap=True,
    )
