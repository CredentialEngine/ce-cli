"""Publisher command group: API publishing to the Credential Registry.

    ce publisher project create --name NAME [--jsonld]
    ce publisher project add --project-id N --file FILE --type credentials
    ce publisher project run validation --project-id N
    ce publisher project show validation status --project-id N
    ce publisher project show validation errors --project-id N
    ce publisher project show status --project-id N
    ce publisher project show audit --project-id N
    ce publisher project complete --project-id N
    ce publisher project list
    ce publisher project abandon --project-id N

This is the developer's overview. The text `ce publisher --help` shows comes from the command docstrings below.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click
from rich.console import Console

from ce.auth.token_manager import require_login
from ce.config.context import DEFAULT_ENVIRONMENTS, require_environment
from ce.publisher import service
from ce.publisher.client import (
    API_PROJECT,
    BULK_UPLOAD_PROJECT,
    REGISTRY_SYNC_PROJECT,
    PublisherApiError,
    PublisherClient,
    project_kind_label,
    resolve_publisher_url,
)

console = Console()
err_console = Console(stderr=True)

_VALIDATION_WAIT_SECONDS = 600
_PUBLISH_WAIT_SECONDS = 900


def _publisher_url_option(f):  # type: ignore[no-untyped-def]
    return click.option(
        "--publisher-url",
        default=None,
        metavar="URL",
        help="Publisher API address. Defaults to the environment's (or CE_PUBLISHER_API_URL).",
    )(f)


def _project_option(f):  # type: ignore[no-untyped-def]
    return click.option(
        "--project-id", "project_id", required=True, type=int, help="The project's number."
    )(f)


def _output_option(f):  # type: ignore[no-untyped-def]
    return click.option(
        "--output",
        "-o",
        "output",
        type=click.Choice(["text", "json"]),
        default="text",
        show_default=True,
        help="Output format.",
    )(f)


@contextmanager
def _client(publisher_url: str | None) -> Iterator[PublisherClient]:
    """A Publisher client for the signed-in user, or exit 1 with the reason."""
    token = require_login()
    name, env = require_environment()
    default = DEFAULT_ENVIRONMENTS.get(name)
    environment_url = env.publisher_api_base or (default.publisher_api_base if default else "")

    try:
        url = resolve_publisher_url(publisher_url, environment_url, name)
    except PublisherApiError as exc:
        _fail(str(exc))

    with PublisherClient(url, token, verify=env.ssl_verify) as client:
        try:
            yield client
        except PublisherApiError as exc:
            _fail(_describe_error(exc))


def _describe_error(exc: PublisherApiError) -> str:
    if exc.status_code == 401:
        return f"{exc} Your session may have expired; run 'ce login'."
    if exc.status_code == 403 and not exc.detail:
        # The Publisher gave no reason: the Publisher user role is missing. When it does give one (only the
        # author may change the project; nobody could be checked as the owner; ...), that reason is the answer.
        return f"{exc} Your account needs the Publisher user role."
    return str(exc)


def _fail(message: str) -> None:
    err_console.print(f"[red]✗[/red] {message}", highlight=False, soft_wrap=True)
    sys.exit(1)


def _echo_json(value: Any) -> None:
    click.echo(json.dumps(value, indent=2))


@click.group("publisher")
def publisher_group() -> None:
    """Publish resources to the Credential Registry through the Publisher.

    \b
    A project collects the files you publish together:
      1. ce publisher project create --name "My project"
      2. ce publisher project add --project-id N --file credentials.csv --type credentials
      3. ce publisher project run validation --project-id N
      4. ce publisher project show validation errors --project-id N
      5. fix the files and add them again, then validate again
      6. ce publisher project complete --project-id N

    \b
    Files are BU template CSVs (a BU project, the default), or JSON-LD in the
    shape the CSV transform produces (create the project with --jsonld).
    """


@publisher_group.group("project")
def project_group() -> None:
    """Create a project, add files, validate them and publish."""


@project_group.command("create")
@click.option("--name", required=True, help="A name to recognise the project by.")
@click.option("--jsonld", is_flag=True,
              help="Create an API publishing project (JSON-LD files only) instead of a BU project.")
@_publisher_url_option
def project_create(name: str, jsonld: bool, publisher_url: str | None) -> None:
    """Create a project: a BU project takes BU template CSVs, an API publishing project takes JSON-LD."""
    if not name.strip():
        _fail("The project needs a name.")

    with _client(publisher_url) as client:
        project_id = client.create_project(name.strip(), jsonld=jsonld)

    console.print(f"Created project {project_id}", highlight=False)


@project_group.command("list")
@_publisher_url_option
def project_list(publisher_url: str | None) -> None:
    """List the projects you can see, newest first."""
    with _client(publisher_url) as client:
        projects = client.list_projects()

    for project in sorted(projects, key=lambda item: int(item.get("projectId", 0)), reverse=True):
        kind = project_kind_label(project.get("projectType"))
        console.print(
            f"{project.get('projectId'):>6}  {kind:<19} {project.get('status', ''):<10} "
            f"{project.get('publishStatus', ''):<13} {project.get('name', '')}",
            highlight=False,
            soft_wrap=True,
        )


@project_group.command("add")
@_project_option
@click.option("--file", "paths", multiple=True, required=True, type=click.Path(path_type=Path),
              help="A file, or a folder of them. Repeat for several.")
@click.option("--type", "template", default=None, metavar="TEMPLATE",
              help="What the CSV files hold, by BU template: credentials, learning-opportunities, "
                   "assessments, ... A command adds files of one template.")
@click.option("--recursive", "-r", is_flag=True, help="Include files in subfolders.")
@_publisher_url_option
def project_add(
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
    with _client(publisher_url) as client:
        project = client.get_project(project_id)
        kind = project.get("projectType")

        try:
            files = service.collect_files(paths, service.extensions_for(kind), recursive=recursive)
            if kind == BULK_UPLOAD_PROJECT:
                resource_class = service.resolve_resource_class(template)
            elif template:
                raise PublisherApiError("--type applies to CSV files; an API publishing project does not take it.")
        except PublisherApiError as exc:
            _fail(str(exc))

        if kind == BULK_UPLOAD_PROJECT:
            result = client.upload_csv(project_id, files, resource_class)
        else:
            result = client.upload_jsonld(project_id, files)

    for path in files:
        console.print(f"[green]✓[/green] Added {path.name}", highlight=False, soft_wrap=True)

    note = " Validation has started." if kind == BULK_UPLOAD_PROJECT else " Run validation when you have added everything."
    console.print(
        f"{len(files)} file(s) in iteration {result.get('iterationId')}.{note}",
        highlight=False,
        soft_wrap=True,
    )


# ce publisher project run validation


@project_group.group("run")
def run_group() -> None:
    """Run a step of a project."""


@run_group.command("validation")
@_project_option
@click.option("--wait/--no-wait", default=True, show_default=True,
              help="Wait until validation has finished.")
@click.option("--timeout", default=_VALIDATION_WAIT_SECONDS, show_default=True, type=int,
              help="Seconds to wait for validation.")
@_publisher_url_option
def run_validation(project_id: int, wait: bool, timeout: int, publisher_url: str | None) -> None:
    """Validate the project's latest iteration, including the CTIDs it refers to.

    \b
    A BU project starts validating when files are added, so for it this only waits for that run and shows its result;
    it never starts a second run. To validate again, add a fixed file (a new iteration). An API publishing project is
    validated only when you run this.
    """
    with _client(publisher_url) as client:
        project_kind = client.get_project(project_id).get("projectType")
        if project_kind == REGISTRY_SYNC_PROJECT:
            _fail(f"Project {project_id} is a Ruby Registry sync, which has no validation step.")

        iteration = client.latest_iteration(project_id)
        if iteration is None:
            _fail(f"Project {project_id} has no files yet. Add some first.")

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

        with console.status("[dim]Validating...[/dim]"):
            summary = service.wait_for_validation(
                client, project_id, iteration_id, timeout_seconds=timeout
            )

    _print_validation_status(summary, verbose=False)
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


# ce publisher project show ...


@project_group.group("show")
def show_group() -> None:
    """Show a project's state, validation results or audit log."""


@show_group.command("status")
@_project_option
@_output_option
@_publisher_url_option
def show_status(project_id: int, output: str, publisher_url: str | None) -> None:
    """Show a project, its latest iteration and its publishing stages."""
    with _client(publisher_url) as client:
        project = client.get_project(project_id)
        iteration = client.latest_iteration(project_id)

    stages = service.latest_stage_jobs(project.get("publishingJobs"))

    if output == "json":
        _echo_json(
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


@show_group.command("audit")
@_project_option
@_output_option
@_publisher_url_option
def show_audit(project_id: int, output: str, publisher_url: str | None) -> None:
    """Show who did what to the project, oldest first."""
    with _client(publisher_url) as client:
        entries = client.get_audit(project_id)

    entries = sorted(entries, key=lambda item: (str(item.get("createdAt", "")), item.get("id", 0)))

    if output == "json":
        _echo_json(entries)
        return

    for entry in entries:
        console.print(
            f"{_short_time(str(entry.get('createdAt', '')))}  "
            f"{entry.get('eventType', ''):<26} {entry.get('description', '')}",
            highlight=False,
            soft_wrap=True,
        )


@show_group.group("validation")
def show_validation_group() -> None:
    """Show the validation results of the project's latest iteration."""


@show_validation_group.command("status")
@_project_option
@click.option("--verbose", "-v", is_flag=True, help="List every file and what was found in it.")
@_output_option
@_publisher_url_option
def show_validation_status(
    project_id: int, verbose: bool, output: str, publisher_url: str | None
) -> None:
    """Show how many files passed validation and how many have errors."""
    with _client(publisher_url) as client:
        summary = service.validation_summary(client, project_id)

    if output == "json":
        result = summary.as_dict()
        if not verbose:
            result.pop("findings")
        _echo_json(result)
        return

    _print_validation_status(summary, verbose=verbose)


@show_validation_group.command("errors")
@_project_option
@_output_option
@_publisher_url_option
def show_validation_errors(project_id: int, output: str, publisher_url: str | None) -> None:
    """Show the validation errors that must be fixed before the project can be completed."""
    with _client(publisher_url) as client:
        summary = service.validation_summary(client, project_id)

    if output == "json":
        _echo_json([item for item in summary.as_dict()["findings"] if item["blocking"]])
        return

    if not summary.validated:
        _print_validation_status(summary, verbose=False)
        return

    for finding in summary.errors:
        console.print(service.format_finding(finding), highlight=False, soft_wrap=True)
    count = len(summary.errors)
    console.print(f"{count} error{'' if count == 1 else 's'}", highlight=False, soft_wrap=True)


def _print_validation_status(summary: service.ValidationSummary, *, verbose: bool) -> None:
    if not summary.validated:
        hint = (
            "Validation is running."
            if summary.status == service.VALIDATING
            else "Validation has not been run on it yet."
        )
        console.print(
            f"Iteration {summary.iteration_id}: {summary.status}, "
            f"{len(summary.files)} file(s). {hint}",
            highlight=False,
        )
        return

    console.print(
        f"Iteration {summary.iteration_id}: {len(summary.valid_files)} succeeded, "
        f"{len(summary.files_with_errors)} with errors.",
        highlight=False,
    )

    if not verbose:
        return

    failed = set(summary.files_with_errors)
    for name in summary.files:
        mark = "[red]✗[/red]" if name in failed else "[green]✓[/green]"
        console.print(f"  {mark} {name}", highlight=False, soft_wrap=True)
        for finding in summary.findings:
            if finding.file_name == name:
                console.print(
                    f"      {service.format_finding(finding, with_file=False)}",
                    highlight=False,
                    soft_wrap=True,
                )


# ce publisher project complete / abandon


@project_group.command("complete")
@_project_option
@click.option("--wait/--no-wait", default=True, show_default=True,
              help="Wait until publishing has finished.")
@click.option("--timeout", default=_PUBLISH_WAIT_SECONDS, show_default=True, type=int,
              help="Seconds to wait for each step.")
@_publisher_url_option
def project_complete(project_id: int, wait: bool, timeout: int, publisher_url: str | None) -> None:
    """Approve the project and publish it to the Registry.

    \b
    The latest iteration must have passed validation without errors.
    A BU project is first transformed to JSON-LD, and you are made a reviewer
    so that you can approve it. Each step is recorded in the audit log.
    Run again to retry a publish that failed.
    """
    with _client(publisher_url) as client:
        user_id = service.user_id_from_token(client.access_token)
        with console.status("[dim]Completing...[/dim]"):
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

    with console.status(f"[dim]Publishing project {project_id}...[/dim]"):
        outcome = service.wait_for_publish(
            client, project_id, timeout_seconds=timeout, on_progress=on_progress
        )

    if outcome.result == "published":
        console.print(f"[green]✓[/green] Project {project_id} is published.", highlight=False)
        return True

    console.print(
        f"[red]✗[/red] Project {project_id} is {outcome.result}. "
        f"See 'ce publisher project show status --project-id {project_id}'.",
        highlight=False,
        soft_wrap=True,
    )
    return False


@project_group.command("abandon")
@_project_option
@click.option("--yes", "-y", is_flag=True, help="Skip the confirmation prompt.")
@_publisher_url_option
def project_abandon(project_id: int, yes: bool, publisher_url: str | None) -> None:
    """Abandon a project that has not been published."""
    if not yes:
        click.confirm(f"  Abandon project {project_id}?", abort=True)

    with _client(publisher_url) as client:
        client.abandon(project_id)

    console.print(f"Project {project_id} is abandoned.", highlight=False)


def _short_time(value: str) -> str:
    """An ISO UTC time from the Publisher as 'yyyy-mm-dd hh:mm:ss UTC', or the value as given."""
    # .NET sends 7 fractional digits; Python before 3.11 reads at most 6.
    text = re.sub(r"(\.\d{6})\d+", r"\1", value).replace("Z", "+00:00")
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return value
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
