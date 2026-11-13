"""Client for the Publisher API calls that API publishing uses.

Requests are built by the client generated from the Publisher's Swagger
document (ce/publisher/api/publisher_client; see generate.ps1). The answers
are read here: the Publisher declares several of them as IActionResult or
sends no body, which the generated parsers cannot read. The two file uploads
are built here too, because the Publisher takes the CSV classifications as
indexed form fields.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType
from typing import Any
from uuid import UUID

import httpx

from ce.publisher.api.publisher_client import AuthenticatedClient
from ce.publisher.api.publisher_client.api.project import (
    get_projects,
    get_projects_project_id,
    get_projects_project_id_audit,
    get_projects_project_id_iterations,
    get_projects_project_id_iterations_iteration_id_files,
    get_projects_project_id_iterations_iteration_id_validation_results,
    get_projects_project_id_reviewers,
    post_projects,
    post_projects_project_id_abandon,
    post_projects_project_id_approve,
    post_projects_project_id_reviewers,
    start_publish,
    start_transform,
    start_validation,
)
from ce.publisher.api.publisher_client.models.add_project_reviewer_dto import (
    AddProjectReviewerDto,
)
from ce.publisher.api.publisher_client.models.project_create_dto import ProjectCreateDto
from ce.publisher.api.publisher_client.models.project_type import ProjectType

PUBLISHER_URL_ENV_VAR = "CE_PUBLISHER_API_URL"

_DEFAULT_TIMEOUT_SECONDS = 120.0

BULK_UPLOAD_PROJECT = "BulkUpload"
REGISTRY_SYNC_PROJECT = "RubyRegistrySync"
API_PROJECT = "ApiPublishing"

_KIND_LABELS = {
    BULK_UPLOAD_PROJECT: "BU",
    REGISTRY_SYNC_PROJECT: "Ruby Registry sync",
    API_PROJECT: "API",
}


def project_kind_label(project_type: str | None) -> str:
    """A short name for a project's type: BU, API or Ruby Registry sync."""
    return _KIND_LABELS.get(project_type or "", project_type or "unknown")


class PublisherApiError(Exception):
    """The Publisher API refused a request or could not be reached."""

    def __init__(self, message: str, status_code: int | None = None, detail: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        # What the Publisher said, without ce-cli's own words around it. Empty when it said nothing.
        self.detail = detail


def resolve_publisher_url(
    explicit_url: str | None,
    environment_url: str | None,
    env_name: str,
    environ: dict[str, str] | None = None,
) -> str:
    """Pick the Publisher API address.

    An address given on the command line wins, then the CE_PUBLISHER_API_URL
    environment variable, then the active environment's publisher_api_base.
    """
    environ = os.environ if environ is None else environ
    url = explicit_url or environ.get(PUBLISHER_URL_ENV_VAR) or environment_url or ""

    if not url:
        raise PublisherApiError(
            f"No Publisher API address is known for environment '{env_name}'. "
            f"Pass --publisher-url or set {PUBLISHER_URL_ENV_VAR}."
        )

    return url.rstrip("/")


class PublisherClient:
    """Calls the Publisher API as the signed-in user."""

    def __init__(
        self,
        base_url: str,
        access_token: str,
        *,
        verify: bool = True,
        transport: httpx.BaseTransport | None = None,
        timeout: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.access_token = access_token
        httpx_args: dict[str, Any] = {} if transport is None else {"transport": transport}
        self._api = AuthenticatedClient(
            base_url=base_url.rstrip("/"),
            token=access_token,
            verify_ssl=verify,
            timeout=httpx.Timeout(timeout),
            headers={"Accept": "application/json", "User-Agent": "ce-cli"},
            httpx_args=httpx_args,
        )

    def close(self) -> None:
        self._api.get_httpx_client().close()

    def __enter__(self) -> PublisherClient:  # noqa: PYI034 - typing.Self needs Python 3.11
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def create_project(self, name: str, *, jsonld: bool = False) -> int:
        """Create a project and return its id.

        A bulk upload (BU) project takes BU template CSV files. An API
        publishing project takes JSON-LD files, and only JSON-LD files, in the
        shape the CSV transform produces. (A Ruby Registry sync project is made
        by the Registry, not by a user.)
        """
        project_type = ProjectType.APIPUBLISHING if jsonld else ProjectType.BULKUPLOAD
        created = self._json(post_projects, body=ProjectCreateDto(name=name, project_type=project_type))
        if not isinstance(created, dict) or "projectId" not in created:
            raise PublisherApiError("The Publisher did not return the new project's id.")
        return int(created["projectId"])

    def list_projects(self) -> list[dict[str, Any]]:
        return self._json(get_projects) or []

    def get_project(self, project_id: int) -> dict[str, Any]:
        return self._json(get_projects_project_id, project_id)

    def get_iterations(self, project_id: int) -> list[dict[str, Any]]:
        return self._json(get_projects_project_id_iterations, project_id) or []

    def latest_iteration(self, project_id: int) -> dict[str, Any] | None:
        """The project's newest iteration, or None when it has none."""
        iterations = self.get_iterations(project_id)
        if not iterations:
            return None
        return max(iterations, key=lambda item: int(item["iterationId"]))

    def get_iteration_files(self, project_id: int, iteration_id: int) -> list[dict[str, Any]]:
        return (
            self._json(
                get_projects_project_id_iterations_iteration_id_files, project_id, iteration_id
            )
            or []
        )

    def get_validation_results(
        self, project_id: int, iteration_id: int, limit_per_file: int = 50
    ) -> dict[str, dict[str, list[dict[str, Any]]]]:
        """Findings as {file name: {finding type: [finding, ...]}}."""
        return (
            self._json(
                get_projects_project_id_iterations_iteration_id_validation_results,
                project_id,
                iteration_id,
                limit_per_file=limit_per_file,
            )
            or {}
        )

    def get_audit(self, project_id: int) -> list[dict[str, Any]]:
        """The project's audit log, newest entry first."""
        return self._json(get_projects_project_id_audit, project_id) or []

    def get_reviewers(self, project_id: int) -> list[dict[str, Any]]:
        return self._json(get_projects_project_id_reviewers, project_id) or []

    # ------------------------------------------------------------------
    # Files
    # ------------------------------------------------------------------

    def upload_csv(
        self, project_id: int, files: Sequence[Path], resource_class: str
    ) -> dict[str, Any]:
        """Add CSV files, all of one resource class, to a BU project.

        The Publisher starts validating the new iteration at once.
        """
        parts = [("Files", (path.name, path.read_bytes(), "text/csv")) for path in files]
        form = {}
        for index, path in enumerate(files):
            form[f"Classifications[{index}].FileName"] = path.name
            form[f"Classifications[{index}].ResourceClass"] = resource_class
        return self._upload(f"/projects/{project_id}/iterations/upload", parts, form)

    def upload_jsonld(self, project_id: int, files: Sequence[Path]) -> dict[str, Any]:
        """Add JSON-LD files to an API publishing project, or replace the files of the same name."""
        parts = [("Files", (path.name, path.read_bytes(), "application/ld+json")) for path in files]
        return self._upload(f"/projects/{project_id}/iterations/upload-jsonld", parts, {})

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------

    def start_validation(self, project_id: int, iteration_id: int) -> None:
        self._request(start_validation, project_id, iteration_id)

    def start_transform(self, project_id: int, iteration_id: int) -> None:
        self._request(start_transform, project_id, iteration_id)

    def add_reviewer(self, project_id: int, user_id: str, *, required: bool = True) -> None:
        self._request(
            post_projects_project_id_reviewers,
            project_id,
            body=AddProjectReviewerDto(user_id=UUID(user_id), is_required=required),
        )

    def approve(self, project_id: int) -> None:
        self._request(post_projects_project_id_approve, project_id)

    def start_publish(self, project_id: int, iteration_id: int) -> None:
        self._request(start_publish, project_id, iteration_id=iteration_id)

    def abandon(self, project_id: int) -> None:
        self._request(post_projects_project_id_abandon, project_id)

    # ------------------------------------------------------------------
    # Transport
    # ------------------------------------------------------------------

    def _upload(
        self, path: str, parts: list[tuple[str, tuple[str, bytes, str]]], form: dict[str, str]
    ) -> dict[str, Any]:
        label = f"POST {path}"
        try:
            response = self._api.get_httpx_client().request("POST", path, files=parts, data=form)
        except httpx.HTTPError as exc:
            raise PublisherApiError(
                f"Could not reach the Publisher at {self._api._base_url}: {exc}"
            ) from exc

        _raise_for_status(label, response)
        payload = _json_or_none(response)
        if not isinstance(payload, dict):
            raise PublisherApiError(
                f"The Publisher answered {label} with something that is not JSON.",
                response.status_code,
            )
        return payload

    def _json(self, endpoint: ModuleType, *args: Any, **kwargs: Any) -> Any:
        response, label = self._send(endpoint, *args, **kwargs)
        _raise_for_status(label, response)

        if not response.content:
            return None

        payload = _json_or_none(response)
        if payload is None:
            raise PublisherApiError(
                f"The Publisher answered {label} with something that is not JSON.",
                response.status_code,
            )
        return payload

    def _request(self, endpoint: ModuleType, *args: Any, **kwargs: Any) -> httpx.Response:
        response, label = self._send(endpoint, *args, **kwargs)
        _raise_for_status(label, response)
        return response

    def _send(
        self, endpoint: ModuleType, *args: Any, **kwargs: Any
    ) -> tuple[httpx.Response, str]:
        """Send the request the generated endpoint module builds."""
        request = endpoint._get_kwargs(*args, **kwargs)
        label = f"{str(request['method']).upper()} {request['url']}"

        try:
            return self._api.get_httpx_client().request(**request), label
        except httpx.HTTPError as exc:
            raise PublisherApiError(
                f"Could not reach the Publisher at {self._api._base_url}: {exc}"
            ) from exc


def _json_or_none(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return None


def _raise_for_status(label: str, response: httpx.Response) -> None:
    if response.status_code < 400:
        return

    body = _json_or_none(response)
    detail = ""
    if isinstance(body, str):
        detail = body
    elif isinstance(body, dict):
        detail = str(body.get("message") or body.get("title") or "")
    if not detail:
        detail = response.text.strip()[:300]

    status = f"{response.status_code} {response.reason_phrase}".strip()
    raise PublisherApiError(
        f"{label} failed ({status}): {detail}".rstrip(": "),
        response.status_code,
        detail,
    )
