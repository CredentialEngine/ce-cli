"""ce publisher project validation run"""

from __future__ import annotations

import sys

import click

from ce.implementations.publisher import service
from ce.implementations.publisher.cli import (
    console,
    fail,
    print_validation_status,
    project_option,
    publisher_client,
    publisher_url_option,
)
from ce.implementations.publisher.client import BULK_UPLOAD_PROJECT, REGISTRY_SYNC_PROJECT

_VALIDATION_WAIT_SECONDS = 600


@click.command("run")
@project_option
@click.option("--wait/--no-wait", default=True, show_default=True,
              help="Wait until validation has finished.")
@click.option("--timeout", default=_VALIDATION_WAIT_SECONDS, show_default=True, type=int,
              help="Seconds to wait for validation.")
@publisher_url_option
def main(project_id: int, wait: bool, timeout: int, publisher_url: str | None) -> None:
    """Validate the project's latest iteration, including the CTIDs it refers to.

    \b
    A BU project starts validating when files are added, so for it this only waits for that run and shows its result;
    it never starts a second run. To validate again, add a fixed file (a new iteration). An API publishing project is
    validated only when you run this.
    """
    with publisher_client(publisher_url) as client:
        project_kind = client.get_project(project_id).get("projectType")
        if project_kind == REGISTRY_SYNC_PROJECT:
            fail(f"Project {project_id} is a Ruby Registry sync, which has no validation step.")

        iteration = client.latest_iteration(project_id)
        if iteration is None:
            fail(f"Project {project_id} has no files yet. Add some first.")

        iteration_id = int(iteration["iterationId"])
        status = str(iteration.get("status", ""))

        if status == "Created":
            client.start_validation(project_id, iteration_id)
            console.print(f"Started validation of iteration {iteration_id}.", highlight=False)
        elif status == service.VALIDATING:
            console.print(_validating_note(project_kind, iteration_id), highlight=False)
        else:
            console.print(_already_validated_note(project_kind, iteration_id), highlight=False)

        if not wait and status in ("Created", service.VALIDATING):
            return

        with console.status("Validating..."):
            summary = service.wait_for_validation(
                client, project_id, iteration_id, timeout_seconds=timeout
            )

    print_validation_status(summary, verbose=False)
    sys.exit(1 if summary.errors else 0)


def _validating_note(project_kind: object, iteration_id: int) -> str:
    if project_kind == BULK_UPLOAD_PROJECT:
        return f"Iteration {iteration_id} is being validated; it started when the files were added."
    return f"Iteration {iteration_id} is being validated."


def _already_validated_note(project_kind: object, iteration_id: int) -> str:
    if project_kind == BULK_UPLOAD_PROJECT:
        return (
            f"Validation of iteration {iteration_id} already ran when the files were added; showing its result. "
            "To validate again, add a fixed file."
        )
    return (
        f"Iteration {iteration_id} has already been validated; showing its result. "
        "To validate again, add or replace a file."
    )
