"""ce publisher project complete"""

from __future__ import annotations

import sys
from typing import Any

import click

from ce.implementations.publisher import service
from ce.implementations.publisher.cli import (
    console,
    project_option,
    publisher_client,
    publisher_url_option,
)
from ce.implementations.publisher.client import PublisherClient

_PUBLISH_WAIT_SECONDS = 900


@click.command("complete")
@project_option
@click.option("--wait/--no-wait", default=True, show_default=True,
              help="Wait until publishing has finished.")
@click.option("--timeout", default=_PUBLISH_WAIT_SECONDS, show_default=True, type=int,
              help="Seconds to wait for each step.")
@publisher_url_option
def main(project_id: int, wait: bool, timeout: int, publisher_url: str | None) -> None:
    """Approve the project and publish it to the Registry.

    \b
    The latest iteration must have passed validation without errors.
    A BU project is first transformed to JSON-LD, and you are made a reviewer
    so that you can approve it. Each step is recorded in the audit log.
    Run again to retry a publish that failed.
    """
    with publisher_client(publisher_url) as client:
        user_id = service.user_id_from_token(client.access_token)
        with console.status("Completing..."):
            service.complete_project(
                client,
                project_id,
                user_id,
                timeout_seconds=timeout,
                on_step=lambda message: console.print(message, highlight=False, soft_wrap=True),
            )

        if wait and not _wait_and_report(client, project_id, timeout):
            sys.exit(1)


def _wait_and_report(client: PublisherClient, project_id: int, timeout: int) -> bool:
    """Wait for publishing and print how it ended. Returns whether it published."""
    seen: dict[str, str] = {}

    def on_progress(project: dict[str, Any]) -> None:
        for job in service.latest_stage_jobs(project.get("publishingJobs")):
            stage, status = str(job.get("stage")), str(job.get("status"))
            if seen.get(stage) != status:
                seen[stage] = status
                console.print(f"  {stage}: {status}", highlight=False)

    with console.status(f"Publishing project {project_id}..."):
        outcome = service.wait_for_publish(
            client, project_id, timeout_seconds=timeout, on_progress=on_progress
        )

    if outcome.result == "published":
        console.print(f"Project {project_id} is published.", highlight=False)
        return True

    console.print(
        f"Error: Project {project_id} is {outcome.result}. "
        f"See 'ce publisher project status show --project-id {project_id}'.",
        highlight=False,
        soft_wrap=True,
    )
    return False
