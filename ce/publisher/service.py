"""Logic behind `ce publisher`, apart from the command wiring."""

from __future__ import annotations

import base64
import json
import re
import time
from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ce.publisher.client import (
    API_PROJECT,
    BULK_UPLOAD_PROJECT,
    REGISTRY_SYNC_PROJECT,
    PublisherApiError,
    PublisherClient,
)

CSV_EXTENSIONS = (".csv",)
JSONLD_EXTENSIONS = (".json", ".jsonld")

# What a CSV file holds, by the name of its BU template: (class, other names it goes by).
CSV_CLASSES: dict[str, tuple[str, tuple[str, ...]]] = {
    "credentials": ("ceterms:Credential", ("credential",)),
    "learning-opportunities": ("ceterms:LearningOpportunity", ("learningopportunity", "learningopportunities", "lopp")),
    "occupations": ("ceterms:Occupation", ("occupation",)),
    "assessments": ("ceterms:Assessment", ("assessment",)),
    "industries": ("ceterms:Industry", ("industry",)),
    "tasks": ("ceterms:Task", ("task",)),
    "jobs": ("ceterms:Job", ("job",)),
    "collections": ("ceterms:Collection", ("collection",)),
    "organization-augmentations": ("ceterms:Organization", ("organization", "organizations")),
    "work-roles": ("ceterms:WorkRole", ("workrole", "workroles")),
    "metrics": ("qdata:Metric", ("metric",)),
    "cost-manifests": ("ceterms:CostManifest", ("costmanifest", "costmanifests")),
    "transfer-value-profiles": ("ceterms:TransferValueProfile", ("transfervalueprofile", "tvp")),
    "outcome-data": ("qdata:DataSetProfile", ("outcomedata", "datasetprofile")),
    "support-services": ("ceterms:SupportService", ("supportservice", "supportservices")),
    "qualifications-frameworks": ("ceterms:QualificationsFramework", ("qualificationsframework",)),
    "alignment-maps": ("ceterms:AlignmentMap", ("alignmentmap", "alignmentmaps")),
    "credential-types": ("ceterms:CredentialType", ("credentialtype", "credentialtypes")),
    "rubrics": ("ceasn:Rubric", ("rubric",)),
    "qa-actions": ("ceterms:CredentialingAction", ("qaaction", "qaactions", "credentialingaction")),
    "organization-suborganizations": (
        "ceterms:CredentialOrganization",
        ("suborganization", "suborganizations", "organizationsuborganization"),
    ),
}

# Findings of these types stop a project. The rest are warnings.
BLOCKING_FINDING_TYPES = frozenset({"JsonLd", "CsvStructure", "CtidReference"})

VALIDATING = "Validating"
VALIDATED = "Validated"
TRANSFORMING = "Transforming"
TRANSFORMED = "Transformed"
ACTIVE = "Active"
APPROVED = "Approved"
COMPLETED = "Completed"
ABANDONED = "Abandoned"
PUBLISHING = "Publishing"
PUBLISHED = "Published"
PUBLISH_FAILED = "PublishFailed"


@dataclass(frozen=True, slots=True)
class Finding:
    file_name: str
    finding_type: str
    row: int
    column: str
    value: str
    message: str

    @property
    def blocking(self) -> bool:
        return self.finding_type in BLOCKING_FINDING_TYPES


@dataclass(slots=True)
class PublishOutcome:
    """How publishing ended: published, failed or abandoned."""

    result: str
    project: dict[str, Any]


@dataclass(slots=True)
class ValidationSummary:
    """One iteration's validation state: its files and what was found in them."""

    iteration_id: int
    status: str
    files: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    @property
    def validated(self) -> bool:
        return self.status in (VALIDATED, TRANSFORMING, TRANSFORMED)

    @property
    def errors(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.blocking]

    @property
    def files_with_errors(self) -> list[str]:
        return sorted({finding.file_name for finding in self.errors})

    @property
    def valid_files(self) -> list[str]:
        failed = set(self.files_with_errors)
        return [name for name in self.files if name not in failed]

    def as_dict(self) -> dict[str, Any]:
        """The summary for -o json."""
        return {
            "iterationId": self.iteration_id,
            "status": self.status,
            "files": len(self.files),
            "valid": len(self.valid_files) if self.validated else None,
            "withErrors": len(self.files_with_errors) if self.validated else None,
            "errors": len(self.errors),
            "findings": [
                {
                    "file": finding.file_name,
                    "row": finding.row,
                    "type": finding.finding_type,
                    "column": finding.column,
                    "value": finding.value,
                    "message": finding.message,
                    "blocking": finding.blocking,
                }
                for finding in self.findings
            ],
        }


def resolve_resource_class(name: str | None) -> str:
    """The class a CSV holds, from its template's name (credentials), a short name (Credential) or the class itself."""
    if not name or not name.strip():
        raise PublisherApiError(
            "A CSV file needs its template: pass --type, for example --type credentials. "
            f"Templates: {', '.join(CSV_CLASSES)}."
        )

    text = name.strip()
    if ":" in text:
        known = {uri for uri, _ in CSV_CLASSES.values()}
        if text in known:
            return text
        raise PublisherApiError(f"'{text}' is not a class a CSV can hold. Templates: {', '.join(CSV_CLASSES)}.")

    wanted = re.sub(r"[^a-z0-9]", "", text.lower())
    for route, (uri, aliases) in CSV_CLASSES.items():
        names = {re.sub(r"[^a-z0-9]", "", route), *aliases}
        if wanted in names:
            return uri

    raise PublisherApiError(f"'{text}' is not a BU template. Templates: {', '.join(CSV_CLASSES)}.")


def extensions_for(project_type: str | None) -> tuple[str, ...]:
    """The file extensions a kind of project takes."""
    if project_type == API_PROJECT:
        return JSONLD_EXTENSIONS
    if project_type == BULK_UPLOAD_PROJECT:
        return CSV_EXTENSIONS
    if project_type == REGISTRY_SYNC_PROJECT:
        raise PublisherApiError(
            "A Ruby Registry sync project is made by the Ruby Registry; ce-cli adds no files to it."
        )
    raise PublisherApiError(f"The project is of type '{project_type}', which ce-cli does not take files for.")


def collect_files(
    paths: Iterable[Path], extensions: tuple[str, ...], *, recursive: bool = False
) -> list[Path]:
    """Expand files and folders into the files to send.

    A folder contributes the files with the right extension directly inside
    it, or in its subfolders too when recursive.
    """
    found: list[Path] = []
    expected = " or ".join(extensions)

    for path in paths:
        if path.is_dir():
            pattern = "**/*" if recursive else "*"
            found.extend(
                sorted(
                    item
                    for item in path.glob(pattern)
                    if item.is_file() and item.name.lower().endswith(extensions)
                )
            )
        elif path.is_file():
            if not path.name.lower().endswith(extensions):
                raise PublisherApiError(
                    f"'{path}' is not a {expected} file, which this project takes."
                )
            found.append(path)
        else:
            raise PublisherApiError(f"'{path}' does not exist.")

    if not found:
        raise PublisherApiError(f"No {expected} files were found.")

    names = [item.name.lower() for item in found]
    if len(set(names)) != len(names):
        raise PublisherApiError("Two of the files have the same name; a project keeps one file per name.")

    return found


def flatten_findings(
    results: dict[str, dict[str, list[dict[str, Any]]]],
) -> list[Finding]:
    """Turn the Publisher's per-file result map into a flat list."""
    findings: list[Finding] = []
    for file_name in sorted(results):
        for finding_type, items in results[file_name].items():
            findings.extend(
                Finding(
                    file_name=file_name,
                    finding_type=finding_type,
                    row=int(item.get("row", 0)),
                    column=str(item.get("column", "")),
                    value=str(item.get("value", "")),
                    message=str(item.get("message", "")),
                )
                for item in items or []
            )
    return findings


def format_finding(finding: Finding, *, with_file: bool = True) -> str:
    """One finding as a line: the file and row, the column, then what is wrong."""
    severity = "error" if finding.blocking else "warning"
    where = f"{finding.column}: " if finding.column else ""
    value = f" ({finding.value})" if finding.value else ""
    if with_file:
        row = f":{finding.row}" if finding.row else ""
        place = f"{finding.file_name}{row}: "
    else:
        place = f"row {finding.row}: " if finding.row else ""
    return f"{place}{where}{severity}: {finding.message}{value}"


def latest_stage_jobs(
    jobs: list[dict[str, Any]] | None,
    ignore_job_ids: Collection[str] = (),
) -> list[dict[str, Any]]:
    """The latest record of each publishing stage.

    A retried publish adds a record per stage and attempt, listed oldest
    first, so a later record replaces an earlier one. Records whose jobId is
    in ignore_job_ids, such as those of an earlier attempt, are left out.
    """
    latest: dict[str, dict[str, Any]] = {}
    for job in jobs or []:
        if job.get("jobId") in ignore_job_ids:
            continue
        latest[str(job["stage"])] = job
    return list(latest.values())


def user_id_from_token(access_token: str) -> str:
    """The signed-in user's id: the subject of the access token.

    The token is only read, not checked: the Publisher checks it on every call.
    """
    try:
        payload = access_token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        subject = json.loads(base64.urlsafe_b64decode(payload))["sub"]
    except (IndexError, ValueError, KeyError, TypeError) as exc:
        raise PublisherApiError(
            "Could not read your user id from the access token. Run 'ce login' again."
        ) from exc
    return str(subject)


def validation_summary(
    client: PublisherClient, project_id: int, iteration_id: int | None = None
) -> ValidationSummary:
    """The validation state of an iteration (the latest by default) and its findings."""
    if iteration_id is None:
        iteration = client.latest_iteration(project_id)
        if iteration is None:
            raise PublisherApiError(
                f"Project {project_id} has no files yet. Add some with "
                f"'ce publisher project add --project-id {project_id} --file <file>'."
            )
    else:
        iteration = next(
            (
                item
                for item in client.get_iterations(project_id)
                if int(item["iterationId"]) == iteration_id
            ),
            None,
        )
        if iteration is None:
            raise PublisherApiError(f"Project {project_id} has no iteration {iteration_id}.")

    number = int(iteration["iterationId"])
    files = sorted(
        str(item.get("fileName", "")) for item in client.get_iteration_files(project_id, number)
    )
    status = str(iteration.get("status", ""))
    summary = ValidationSummary(iteration_id=number, status=status, files=files)

    if summary.validated:
        summary.findings = flatten_findings(client.get_validation_results(project_id, number))

    return summary


def _wait_for_iteration(
    client: PublisherClient,
    project_id: int,
    iteration_id: int,
    reached: Callable[[str], bool],
    *,
    timeout_seconds: float,
    poll_seconds: float,
    sleep: Callable[[float], None],
    clock: Callable[[], float],
    stuck_hint: str,
) -> str:
    """Wait until the iteration's status satisfies `reached`, and return it."""
    deadline = clock() + timeout_seconds

    while True:
        iteration = next(
            (
                item
                for item in client.get_iterations(project_id)
                if int(item["iterationId"]) == iteration_id
            ),
            None,
        )
        status = str(iteration.get("status", "")) if iteration else ""
        if reached(status):
            return status

        if clock() >= deadline:
            raise PublisherApiError(
                f"Iteration {iteration_id} of project {project_id} is still {status or 'not found'} "
                f"after {timeout_seconds:.0f} seconds. {stuck_hint}"
            )
        sleep(poll_seconds)


def wait_for_validation(
    client: PublisherClient,
    project_id: int,
    iteration_id: int,
    *,
    timeout_seconds: float,
    poll_seconds: float = 3.0,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> ValidationSummary:
    """Wait until the iteration is validated and return its findings."""
    _wait_for_iteration(
        client,
        project_id,
        iteration_id,
        lambda status: status in (VALIDATED, TRANSFORMING, TRANSFORMED),
        timeout_seconds=timeout_seconds,
        poll_seconds=poll_seconds,
        sleep=sleep,
        clock=clock,
        stuck_hint=(
            "The validation job may have failed. "
            f"Check with 'ce publisher project show validation status --project-id {project_id}'."
        ),
    )
    return validation_summary(client, project_id, iteration_id)


def wait_for_transform(
    client: PublisherClient,
    project_id: int,
    iteration_id: int,
    *,
    timeout_seconds: float,
    poll_seconds: float = 3.0,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> None:
    """Wait until the iteration's CSV files have been transformed to JSON-LD."""
    _wait_for_iteration(
        client,
        project_id,
        iteration_id,
        lambda status: status == TRANSFORMED,
        timeout_seconds=timeout_seconds,
        poll_seconds=poll_seconds,
        sleep=sleep,
        clock=clock,
        stuck_hint=(
            "The transform job may have failed. "
            f"Check with 'ce publisher project show status --project-id {project_id}'."
        ),
    )


def wait_for_publish(
    client: PublisherClient,
    project_id: int,
    *,
    timeout_seconds: float,
    poll_seconds: float = 5.0,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
    on_progress: Callable[[dict[str, Any]], None] | None = None,
) -> PublishOutcome:
    """Wait until a completed project is published, fails or is abandoned."""
    deadline = clock() + timeout_seconds

    while True:
        project = client.get_project(project_id)
        if on_progress is not None:
            on_progress(project)

        if project.get("status") == COMPLETED:
            return PublishOutcome("published", project)
        if project.get("publishStatus") == PUBLISH_FAILED:
            return PublishOutcome("failed", project)
        if project.get("status") == ABANDONED:
            return PublishOutcome("abandoned", project)

        if clock() >= deadline:
            raise PublisherApiError(
                f"Project {project_id} is still not published after "
                f"{timeout_seconds:.0f} seconds. Check again with "
                f"'ce publisher project show status --project-id {project_id}'."
            )
        sleep(poll_seconds)


def complete_project(
    client: PublisherClient,
    project_id: int,
    user_id: str,
    *,
    timeout_seconds: float,
    on_step: Callable[[str], None],
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> int:
    """Take a validated project to the point where publishing has started, and return the iteration.

    The steps, each recorded in the project's audit log:
    1. a BU project's CSV files are transformed to JSON-LD;
    2. the project is approved, as you (a BU project first makes you a reviewer);
    3. publishing starts.
    Run again after a publish that failed, it only starts publishing again.
    """
    project = client.get_project(project_id)
    kind = project.get("projectType")
    status = project.get("status")
    publish_status = project.get("publishStatus")

    if kind == REGISTRY_SYNC_PROJECT:
        raise PublisherApiError(
            f"Project {project_id} is a Ruby Registry sync, which the Ruby Registry publishes. ce-cli does not."
        )

    if status == ABANDONED:
        raise PublisherApiError(f"Project {project_id} was abandoned.")
    if status == COMPLETED or publish_status in (PUBLISHING, PUBLISHED):
        raise PublisherApiError(
            f"Project {project_id} is already {publish_status or status}. "
            f"See 'ce publisher project show status --project-id {project_id}'."
        )

    iteration = client.latest_iteration(project_id)
    if iteration is None:
        raise PublisherApiError(f"Project {project_id} has no files yet. Add some first.")
    iteration_id = int(iteration["iterationId"])
    iteration_status = str(iteration.get("status", ""))

    if status == ACTIVE:
        _prepare_for_approval(
            client, project, kind, iteration_id, iteration_status, user_id, timeout_seconds,
            on_step, sleep, clock,
        )
        on_step(f"Approving project {project_id}.")
        client.approve(project_id)

    on_step(f"Publishing iteration {iteration_id}.")
    client.start_publish(project_id, iteration_id)
    return iteration_id


def _prepare_for_approval(
    client: PublisherClient,
    project: dict[str, Any],
    kind: str | None,
    iteration_id: int,
    iteration_status: str,
    user_id: str,
    timeout_seconds: float,
    on_step: Callable[[str], None],
    sleep: Callable[[float], None],
    clock: Callable[[], float],
) -> None:
    project_id = int(project["projectId"])

    if iteration_status == VALIDATING:
        raise PublisherApiError(
            f"Iteration {iteration_id} is still being validated. Wait for it, then complete the project."
        )
    if iteration_status not in (VALIDATED, TRANSFORMED):
        raise PublisherApiError(
            f"Iteration {iteration_id} is {iteration_status}, so it has not been validated. Run "
            f"'ce publisher project run validation --project-id {project_id}' first."
        )

    if iteration_status == VALIDATED:
        errors = validation_summary(client, project_id, iteration_id).errors
        if errors:
            raise PublisherApiError(
                f"Validation found {len(errors)} error(s) in iteration {iteration_id}. See them with "
                f"'ce publisher project show validation errors --project-id {project_id}', fix the files "
                "and add them again."
            )

    if kind == BULK_UPLOAD_PROJECT:
        if iteration_status == VALIDATED:
            on_step(f"Transforming the CSV files of iteration {iteration_id} to JSON-LD.")
            client.start_transform(project_id, iteration_id)
            wait_for_transform(
                client, project_id, iteration_id,
                timeout_seconds=timeout_seconds, sleep=sleep, clock=clock,
            )

        reviewers = {str(item.get("userId", "")).lower() for item in project.get("reviewers") or []}
        if user_id.lower() not in reviewers:
            on_step("Adding you as the project's reviewer, so you can approve it.")
            client.add_reviewer(project_id, user_id)
