"""ce publisher project status show"""

from __future__ import annotations

import click

from ce.implementations.publisher import service
from ce.implementations.publisher.cli import (
    console,
    echo_json,
    output_option,
    project_option,
    publisher_client,
    publisher_url_option,
)
from ce.implementations.publisher.client import project_kind_label


@click.command("show")
@project_option
@output_option
@publisher_url_option
def main(project_id: int, output: str, publisher_url: str | None) -> None:
    """Show a project, its latest iteration and its publishing stages."""
    with publisher_client(publisher_url) as client:
        project = client.get_project(project_id)
        iteration = client.latest_iteration(project_id)

    stages = service.latest_stage_jobs(project.get("publishingJobs"))

    if output == "json":
        echo_json(
            {
                "projectId": project_id,
                "name": project.get("name"),
                "projectType": project.get("projectType"),
                "status": project.get("status"),
                "publishStatus": project.get("publishStatus"),
                "iteration": iteration,
                "stages": stages,
            }
        )
        return

    kind = project_kind_label(project.get("projectType"))
    console.print(f"Project {project_id}: {project.get('name', '')} ({kind})", highlight=False)
    console.print(
        f"  Status: {project.get('status')}, publishing: {project.get('publishStatus')}",
        highlight=False,
    )
    if iteration is not None:
        console.print(
            f"  Iteration {iteration.get('iterationId')}: {iteration.get('status')}",
            highlight=False,
        )
    for job in stages:
        error = f" ({job.get('errorMessage')})" if job.get("errorMessage") else ""
        console.print(f"  {job.get('stage')}: {job.get('status')}{error}", highlight=False)
