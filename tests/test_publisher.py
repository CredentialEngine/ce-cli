"""Unit tests for ce publisher: the service functions, the client and the commands.

Run with:
    pytest -m unit tests/test_publisher.py
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest
from click.testing import CliRunner

from ce.commands.publisher import publisher_group
from ce.publisher import service
from ce.publisher.client import (
    PublisherApiError,
    PublisherClient,
    resolve_publisher_url,
    project_kind_label,
)
from ce.publisher.prepare_openapi import keep_json_content

pytestmark = pytest.mark.unit

USER_ID = "61cf1c53-4e26-4be9-81c5-5e623847bfc0"
OTHER_USER_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def make_token(subject: str = USER_ID) -> str:
    def part(value: dict[str, Any]) -> str:
        return base64.urlsafe_b64encode(json.dumps(value).encode()).rstrip(b"=").decode()

    return f"{part({'alg': 'none'})}.{part({'sub': subject})}.signature"


def finding(message: str = "No resource with this CTID was found.", column: str = "Offered By") -> dict[str, Any]:
    return {"row": 3, "column": column, "value": "ce-1", "message": message}


class FakePublisher:
    """A Publisher API in memory, answering the calls ce publisher makes."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.project: dict[str, Any] = {
            "projectId": 7,
            "name": "Welding",
            "projectType": "BulkUpload",
            "status": "Active",
            "publishStatus": "NotPublished",
            "reviewers": [],
            "publishingJobs": [{"jobId": "1", "stage": "ChangesetGeneration", "status": "Succeeded"}],
        }
        self.iterations: list[dict[str, Any]] = [{"iterationId": 1, "status": "Validated"}]
        self.files: list[dict[str, Any]] = [{"fileName": "credentials.csv"}, {"fileName": "jobs.csv"}]
        self.findings: dict[str, Any] = {}
        self.audit: list[dict[str, Any]] = [
            {"id": 2, "createdAt": "2026-11-12T10:00:05.1234567Z", "eventType": "IterationFilesAdded",
             "description": "Added 2 file(s) to Iteration 1."},
            {"id": 1, "createdAt": "2026-11-12T10:00:00Z", "eventType": "ProjectCreated",
             "description": "Created project 'Welding'"},
        ]

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path, method = request.url.path, request.method

        if path == "/projects" and method == "POST":
            return httpx.Response(200, json={"projectId": 7})
        if path == "/projects":
            return httpx.Response(200, json=[self.project])
        if path == "/projects/7":
            return httpx.Response(200, json=self.project)
        if path == "/projects/7/iterations":
            return httpx.Response(200, json=self.iterations)
        if path == "/projects/7/iterations/1/files":
            return httpx.Response(200, json=self.files)
        if path.endswith("/validationResults"):
            return httpx.Response(200, json=self.findings)
        if path == "/projects/7/audit":
            return httpx.Response(200, json=self.audit)
        if path in ("/projects/7/iterations/upload", "/projects/7/iterations/upload-jsonld"):
            return httpx.Response(200, json={"iterationId": 2, "status": "Created"})
        if path == "/projects/7/iterations/1/validation/start":
            self.iterations[0]["status"] = "Validating"
            return httpx.Response(200)
        if path == "/projects/7/iterations/1/transform":
            self.iterations[0]["status"] = "Transformed"
            return httpx.Response(200)
        if path == "/projects/7/reviewers" and method == "POST":
            self.project["reviewers"].append({"userId": json.loads(request.content)["userId"]})
            return httpx.Response(204)
        if path == "/projects/7/approve":
            self.project["status"] = "Approved"
            return httpx.Response(200)
        if path == "/projects/7/publish/start":
            self.project["status"] = "Completed"
            self.project["publishStatus"] = "Published"
            return httpx.Response(200)
        if path == "/projects/7/abandon":
            return httpx.Response(200)
        return httpx.Response(404, json={"title": "Not Found"})

    def client(self, base_url: str = "http://publisher", token: str = "", **_: Any) -> PublisherClient:
        return PublisherClient(
            base_url, token or make_token(), transport=httpx.MockTransport(self.handler)
        )

    def paths(self) -> list[str]:
        return [f"{request.method} {request.url.path}" for request in self.requests]


@pytest.fixture
def publisher() -> FakePublisher:
    return FakePublisher()


@pytest.fixture
def cli(publisher: FakePublisher):
    env = MagicMock()
    env.publisher_api_base = "http://publisher"
    env.ssl_verify = True

    with patch("ce.commands.publisher.require_login", return_value=make_token()), \
            patch("ce.commands.publisher.require_environment", return_value=("dev", env)), \
            patch("ce.commands.publisher.PublisherClient", side_effect=publisher.client), \
            patch("ce.publisher.service.time.sleep"):
        yield CliRunner()


def csv_file(tmp_path: Path, name: str = "credentials.csv") -> Path:
    path = tmp_path / name
    path.write_text("Name,Description\nWelding,A certificate\n")
    return path


def jsonld_file(tmp_path: Path, name: str = "welding.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps([{"@id": "x", "@graph": []}]))
    return path


def run(cli: CliRunner, *args: str, input: str | None = None):
    return cli.invoke(publisher_group, list(args), input=input)


# --- service: what a file is --------------------------------------------------


@pytest.mark.parametrize(
    ("name", "uri"),
    [
        ("credentials", "ceterms:Credential"),
        ("Credential", "ceterms:Credential"),
        ("learning-opportunities", "ceterms:LearningOpportunity"),
        ("Learning Opportunity", "ceterms:LearningOpportunity"),
        ("qa-actions", "ceterms:CredentialingAction"),
        ("outcome-data", "qdata:DataSetProfile"),
        ("rubrics", "ceasn:Rubric"),
        ("ceterms:Assessment", "ceterms:Assessment"),
    ],
)
def test_resolve_resource_class_takes_template_names_short_names_and_classes(name: str, uri: str) -> None:
    assert service.resolve_resource_class(name) == uri


@pytest.mark.parametrize("name", [None, "", "  "])
def test_resolve_resource_class_needs_a_template(name: str | None) -> None:
    with pytest.raises(PublisherApiError, match="--type"):
        service.resolve_resource_class(name)


@pytest.mark.parametrize("name", ["spaceships", "ceterms:Spaceship"])
def test_resolve_resource_class_names_the_templates_when_it_does_not_know_one(name: str) -> None:
    with pytest.raises(PublisherApiError, match="credentials, learning-opportunities"):
        service.resolve_resource_class(name)


def test_every_template_has_a_distinct_class_and_a_name_that_resolves_to_it() -> None:
    for route, (uri, aliases) in service.CSV_CLASSES.items():
        assert service.resolve_resource_class(route) == uri
        assert all(service.resolve_resource_class(alias) == uri for alias in aliases)
    assert len({uri for uri, _ in service.CSV_CLASSES.values()}) == len(service.CSV_CLASSES)


def test_extensions_follow_the_kind_of_project() -> None:
    assert service.extensions_for("BulkUpload") == (".csv",)
    assert service.extensions_for("ApiPublishing") == (".json", ".jsonld")
    with pytest.raises(PublisherApiError, match="does not take files"):
        service.extensions_for("Other")
    with pytest.raises(PublisherApiError, match="Ruby Registry sync project is made by the Ruby Registry"):
        service.extensions_for("RubyRegistrySync")


def test_project_kinds_have_short_names() -> None:
    assert project_kind_label("BulkUpload") == "BU"
    assert project_kind_label("ApiPublishing") == "API"
    assert project_kind_label("RubyRegistrySync") == "Ruby Registry sync"
    assert project_kind_label("Something") == "Something"
    assert project_kind_label(None) == "unknown"


def test_a_ruby_registry_sync_project_takes_no_work_from_ce_cli(
    cli: CliRunner, publisher: FakePublisher, tmp_path: Path
) -> None:
    publisher.project["projectType"] = "RubyRegistrySync"

    added = run(cli, "project", "add", "--project-id", "7", "--file", str(csv_file(tmp_path)), "--type", "credentials")
    validated = run(cli, "project", "run", "validation", "--project-id", "7")
    completed = run(cli, "project", "complete", "--project-id", "7")

    assert added.exit_code == 1 and "Ruby Registry sync" in added.output
    assert validated.exit_code == 1 and "no validation step" in validated.output
    assert completed.exit_code == 1 and "Ruby Registry publishes" in completed.output
    assert not any(request.method == "POST" for request in publisher.requests)


def test_collect_files_takes_the_right_files_from_a_folder(tmp_path: Path) -> None:
    (tmp_path / "a.csv").write_text("x")
    (tmp_path / "B.CSV").write_text("x")
    (tmp_path / "notes.txt").write_text("x")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.csv").write_text("x")

    assert sorted(p.name for p in service.collect_files([tmp_path], (".csv",))) == ["B.CSV", "a.csv"]
    assert len(service.collect_files([tmp_path], (".csv",), recursive=True)) == 3


def test_collect_files_refuses_a_file_of_the_wrong_kind_a_missing_file_and_nothing(tmp_path: Path) -> None:
    with pytest.raises(PublisherApiError, match="is not a .csv file"):
        service.collect_files([jsonld_file(tmp_path)], (".csv",))
    with pytest.raises(PublisherApiError, match="does not exist"):
        service.collect_files([tmp_path / "nope.csv"], (".csv",))
    with pytest.raises(PublisherApiError, match="No .csv files"):
        service.collect_files([tmp_path], (".csv",))


def test_collect_files_refuses_two_files_of_the_same_name(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    first, second = csv_file(tmp_path / "a"), csv_file(tmp_path / "b")

    with pytest.raises(PublisherApiError, match="same name"):
        service.collect_files([first, second], (".csv",))


def test_user_id_is_the_subject_of_the_access_token() -> None:
    assert service.user_id_from_token(make_token()) == USER_ID


@pytest.mark.parametrize("token", ["", "abc", "a.b.c", "a." + base64.b64encode(b"[]").decode() + ".c"])
def test_user_id_from_a_token_that_is_not_a_jwt_is_an_error(token: str) -> None:
    with pytest.raises(PublisherApiError, match="ce login"):
        service.user_id_from_token(token)


# --- service: findings and waits ---------------------------------------------


def test_format_finding_names_the_file_row_column_and_value() -> None:
    item = service.flatten_findings({"credentials.csv": {"CtidReference": [finding("Missing.")]}})[0]

    assert service.format_finding(item) == "credentials.csv:3: Offered By: error: Missing. (ce-1)"
    assert service.format_finding(item, with_file=False) == "row 3: Offered By: error: Missing. (ce-1)"


def test_a_spell_check_finding_is_a_warning() -> None:
    item = service.flatten_findings({"jobs.csv": {"SpellCheck": [finding("Typo.", "Name")]}})[0]

    assert not item.blocking
    assert "warning" in service.format_finding(item)


def test_latest_stage_jobs_keeps_the_newest_attempt() -> None:
    jobs = [
        {"jobId": "1", "stage": "ChangesetGeneration", "status": "Failed"},
        {"jobId": "2", "stage": "ChangesetGeneration", "status": "Succeeded"},
    ]

    assert service.latest_stage_jobs(jobs) == [jobs[1]]
    assert service.latest_stage_jobs(jobs, {"2"}) == [jobs[0]]


def test_validation_summary_counts_files_with_and_without_errors(publisher: FakePublisher) -> None:
    publisher.findings = {"credentials.csv": {"CtidReference": [finding(), finding("Wrong class.")]}}

    summary = service.validation_summary(publisher.client(), 7)

    assert summary.validated
    assert summary.files_with_errors == ["credentials.csv"]
    assert summary.valid_files == ["jobs.csv"]
    assert len(summary.errors) == 2
    assert summary.as_dict()["findings"][0]["file"] == "credentials.csv"


def test_a_transformed_iteration_still_has_its_validation_results(publisher: FakePublisher) -> None:
    publisher.iterations = [{"iterationId": 1, "status": "Transformed"}]

    assert service.validation_summary(publisher.client(), 7).validated


def test_validation_summary_has_no_findings_before_validation(publisher: FakePublisher) -> None:
    publisher.iterations = [{"iterationId": 1, "status": "Created"}]

    summary = service.validation_summary(publisher.client(), 7)

    assert not summary.validated
    assert summary.as_dict()["valid"] is None
    assert "GET /projects/7/iterations/1/validationResults" not in publisher.paths()


def test_validation_summary_needs_an_iteration(publisher: FakePublisher) -> None:
    publisher.iterations = []

    with pytest.raises(PublisherApiError, match="no files yet"):
        service.validation_summary(publisher.client(), 7)

    with pytest.raises(PublisherApiError, match="no iteration 3"):
        service.validation_summary(publisher.client(), 7, 3)


def test_wait_for_validation_times_out_with_a_hint(publisher: FakePublisher) -> None:
    publisher.iterations = [{"iterationId": 1, "status": "Validating"}]
    ticks = iter([0.0, 10.0])

    with pytest.raises(PublisherApiError, match="may have failed"):
        service.wait_for_validation(
            publisher.client(), 7, 1, timeout_seconds=5, sleep=lambda _: None, clock=lambda: next(ticks)
        )


def test_wait_for_transform_times_out_with_a_hint(publisher: FakePublisher) -> None:
    publisher.iterations = [{"iterationId": 1, "status": "Transforming"}]
    ticks = iter([0.0, 10.0])

    with pytest.raises(PublisherApiError, match="transform job may have failed"):
        service.wait_for_transform(
            publisher.client(), 7, 1, timeout_seconds=5, sleep=lambda _: None, clock=lambda: next(ticks)
        )


def test_wait_for_publish_reports_a_failed_publish(publisher: FakePublisher) -> None:
    publisher.project = {"projectId": 7, "status": "Approved", "publishStatus": "PublishFailed"}

    outcome = service.wait_for_publish(publisher.client(), 7, timeout_seconds=5, sleep=lambda _: None)

    assert outcome.result == "failed"


def test_wait_for_publish_times_out(publisher: FakePublisher) -> None:
    publisher.project = {"projectId": 7, "status": "Approved", "publishStatus": "Publishing"}
    ticks = iter([0.0, 10.0])

    with pytest.raises(PublisherApiError, match="still not published"):
        service.wait_for_publish(
            publisher.client(), 7, timeout_seconds=5, sleep=lambda _: None, clock=lambda: next(ticks)
        )


# --- service: completing a project --------------------------------------------


def complete(publisher: FakePublisher, user_id: str = USER_ID) -> tuple[int, list[str]]:
    steps: list[str] = []
    iteration = service.complete_project(
        publisher.client(), 7, user_id, timeout_seconds=5, on_step=steps.append, sleep=lambda _: None
    )
    return iteration, steps


def test_completing_a_csv_project_transforms_makes_you_a_reviewer_approves_and_publishes(
    publisher: FakePublisher,
) -> None:
    iteration, steps = complete(publisher)

    assert iteration == 1
    assert publisher.paths()[-5:] == [
        "POST /projects/7/iterations/1/transform",
        "GET /projects/7/iterations",
        "POST /projects/7/reviewers",
        "POST /projects/7/approve",
        "POST /projects/7/publish/start",
    ]
    assert json.loads(next(r for r in publisher.requests if r.url.path.endswith("/reviewers")).content) == {
        "userId": USER_ID,
        "isRequired": True,
    }
    assert any("Transforming" in step for step in steps)
    assert any("reviewer" in step for step in steps)
    assert steps[-1] == "Publishing iteration 1."


def test_a_reviewer_is_not_added_twice(publisher: FakePublisher) -> None:
    publisher.project["reviewers"] = [{"userId": USER_ID.upper()}]

    complete(publisher)

    assert "POST /projects/7/reviewers" not in publisher.paths()


def test_a_csv_project_that_is_already_transformed_is_not_transformed_again(publisher: FakePublisher) -> None:
    publisher.iterations = [{"iterationId": 1, "status": "Transformed"}]

    complete(publisher)

    assert not any(path.endswith("/transform") for path in publisher.paths())
    assert "POST /projects/7/approve" in publisher.paths()


def test_completing_a_json_ld_project_approves_and_publishes_without_a_transform(publisher: FakePublisher) -> None:
    publisher.project["projectType"] = "ApiPublishing"

    complete(publisher)

    assert publisher.paths()[-2:] == ["POST /projects/7/approve", "POST /projects/7/publish/start"]
    assert not any(path.endswith(("/transform", "/reviewers")) for path in publisher.paths())


def test_completing_is_refused_while_validation_found_errors(publisher: FakePublisher) -> None:
    publisher.findings = {"credentials.csv": {"CsvStructure": [finding("Bad header.", "Name")]}}

    with pytest.raises(PublisherApiError, match="found 1 error"):
        complete(publisher)

    assert "POST /projects/7/approve" not in publisher.paths()


@pytest.mark.parametrize(
    ("status", "message"),
    [("Validating", "still being validated"), ("Created", "has not been validated")],
)
def test_completing_is_refused_before_validation_has_finished(
    publisher: FakePublisher, status: str, message: str
) -> None:
    publisher.iterations = [{"iterationId": 1, "status": status}]

    with pytest.raises(PublisherApiError, match=message):
        complete(publisher)


def test_completing_a_project_that_has_no_files_is_refused(publisher: FakePublisher) -> None:
    publisher.iterations = []

    with pytest.raises(PublisherApiError, match="no files yet"):
        complete(publisher)


def test_completing_again_after_a_failed_publish_only_starts_publishing(publisher: FakePublisher) -> None:
    publisher.project.update({"status": "Approved", "publishStatus": "PublishFailed"})
    publisher.iterations = [{"iterationId": 1, "status": "Transformed"}]

    complete(publisher)

    assert publisher.paths()[-1] == "POST /projects/7/publish/start"
    assert "POST /projects/7/approve" not in publisher.paths()


@pytest.mark.parametrize(
    ("project", "message"),
    [
        ({"status": "Abandoned"}, "was abandoned"),
        ({"status": "Completed", "publishStatus": "Published"}, "already Published"),
        ({"status": "Approved", "publishStatus": "Publishing"}, "already Publishing"),
    ],
)
def test_completing_a_project_that_is_past_that_is_refused(
    publisher: FakePublisher, project: dict[str, str], message: str
) -> None:
    publisher.project.update(project)

    with pytest.raises(PublisherApiError, match=message):
        complete(publisher)


# --- client -------------------------------------------------------------------


def test_resolve_publisher_url_prefers_the_command_line() -> None:
    env = {"CE_PUBLISHER_API_URL": "http://from-env/"}

    assert resolve_publisher_url("http://cli/", "http://config", "dev", env) == "http://cli"
    assert resolve_publisher_url(None, "http://config", "dev", env) == "http://from-env"
    assert resolve_publisher_url(None, "http://config/", "dev", {}) == "http://config"


def test_resolve_publisher_url_needs_an_address() -> None:
    with pytest.raises(PublisherApiError, match="--publisher-url"):
        resolve_publisher_url(None, "", "custom", {})


def test_create_project_makes_a_csv_project_unless_asked_for_json_ld(publisher: FakePublisher) -> None:
    assert publisher.client().create_project("Welding") == 7
    assert publisher.client().create_project("Welding", jsonld=True) == 7

    bodies = [json.loads(request.content) for request in publisher.requests]
    assert bodies == [
        {"name": "Welding", "projectType": "BulkUpload"},
        {"name": "Welding", "projectType": "ApiPublishing"},
    ]


def test_upload_csv_sends_the_files_and_what_each_holds(publisher: FakePublisher, tmp_path: Path) -> None:
    first, second = csv_file(tmp_path, "a.csv"), csv_file(tmp_path, "b.csv")

    result = publisher.client().upload_csv(7, [first, second], "ceterms:Credential")

    request = publisher.requests[0]
    body = request.content.decode()
    assert result["iterationId"] == 2
    assert request.url.path == "/projects/7/iterations/upload"
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert 'name="Files"; filename="a.csv"' in body
    assert 'name="Files"; filename="b.csv"' in body
    assert 'name="Classifications[0].FileName"' in body and "\r\n\r\na.csv\r\n" in body
    assert 'name="Classifications[1].ResourceClass"' in body
    assert body.count("ceterms:Credential") == 2
    assert request.headers["Authorization"].startswith("Bearer ")


def test_upload_jsonld_sends_the_files(publisher: FakePublisher, tmp_path: Path) -> None:
    publisher.client().upload_jsonld(7, [jsonld_file(tmp_path)])

    request = publisher.requests[0]
    assert request.url.path == "/projects/7/iterations/upload-jsonld"
    assert 'name="Files"; filename="welding.json"' in request.content.decode()


def test_a_refused_upload_raises_with_the_reason(publisher: FakePublisher, tmp_path: Path) -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json="Only the project's author can change an API publishing project.")

    client = PublisherClient("http://publisher", make_token(), transport=httpx.MockTransport(refuse))

    with pytest.raises(PublisherApiError, match="Only the project's author") as error:
        client.upload_jsonld(7, [jsonld_file(tmp_path)])

    assert error.value.status_code == 403


def test_other_failures_raise_with_the_status(publisher: FakePublisher) -> None:
    with pytest.raises(PublisherApiError) as error:
        publisher.client().get_iteration_files(9, 1)

    assert error.value.status_code == 404


def test_the_client_has_no_call_for_the_legacy_registry_assistant() -> None:
    names = set(dir(PublisherClient))

    assert names.isdisjoint({"assistant", "format_resource", "add_resource", "complete"})


def test_keep_json_content_drops_the_other_content_types() -> None:
    document = {
        "paths": {
            "/a": {
                "post": {
                    "requestBody": {"content": {"text/json": {}, "application/json": {"x": 1}}},
                    "responses": {
                        "200": {"content": {"text/plain": {}, "application/json": {"y": 2}}},
                        "204": {},
                        "415": {"content": {"application/zip": {}}},
                    },
                }
            }
        }
    }

    operation = keep_json_content(document)["paths"]["/a"]["post"]

    assert operation["requestBody"]["content"] == {"application/json": {"x": 1}}
    assert operation["responses"]["200"]["content"] == {"application/json": {"y": 2}}
    assert operation["responses"]["415"]["content"] == {"application/zip": {}}


# --- commands -----------------------------------------------------------------


def test_the_commands_do_not_offer_the_legacy_registry_assistant(cli: CliRunner) -> None:
    help_text = run(cli).output + run(cli, "project", "--help").output + run(cli, "project", "add", "--help").output

    assert run(cli, "format", "x.json").exit_code == 2
    assert "Registry Assistant" not in help_text
    assert "format" not in run(cli).output.split("Commands:")[1]


def test_create_makes_a_csv_project_by_default(cli: CliRunner, publisher: FakePublisher) -> None:
    result = run(cli, "project", "create", "--name", "Welding")

    assert result.exit_code == 0, result.output
    assert "Created project 7" in result.output
    assert json.loads(publisher.requests[0].content)["projectType"] == "BulkUpload"


def test_create_with_jsonld_makes_a_json_ld_project(cli: CliRunner, publisher: FakePublisher) -> None:
    run(cli, "project", "create", "--name", "Welding", "--jsonld")

    assert json.loads(publisher.requests[0].content)["projectType"] == "ApiPublishing"


def test_list_shows_the_kind_of_each_project(cli: CliRunner, publisher: FakePublisher) -> None:
    result = run(cli, "project", "list")

    assert "BU" in result.output and "Welding" in result.output


def test_add_sends_csv_files_with_their_template(cli: CliRunner, publisher: FakePublisher, tmp_path: Path) -> None:
    result = run(
        cli, "project", "add", "--project-id", "7", "--file", str(csv_file(tmp_path)), "--type", "credentials"
    )

    assert result.exit_code == 0, result.output
    assert "POST /projects/7/iterations/upload" in publisher.paths()
    assert "ceterms:Credential" in publisher.requests[-1].content.decode()
    assert "Added credentials.csv" in result.output
    assert "1 file(s) in iteration 2. Validation has started." in result.output


def test_add_needs_the_template_of_csv_files(cli: CliRunner, publisher: FakePublisher, tmp_path: Path) -> None:
    result = run(cli, "project", "add", "--project-id", "7", "--file", str(csv_file(tmp_path)))

    assert result.exit_code == 1
    assert "--type" in result.output
    assert "POST /projects/7/iterations/upload" not in publisher.paths()


def test_add_refuses_json_ld_files_for_a_csv_project(cli: CliRunner, publisher: FakePublisher, tmp_path: Path) -> None:
    result = run(
        cli, "project", "add", "--project-id", "7", "--file", str(jsonld_file(tmp_path)), "--type", "credentials"
    )

    assert result.exit_code == 1
    assert "is not a .csv file" in result.output


def test_add_sends_json_ld_files_to_a_json_ld_project(
    cli: CliRunner, publisher: FakePublisher, tmp_path: Path
) -> None:
    publisher.project["projectType"] = "ApiPublishing"

    result = run(cli, "project", "add", "--project-id", "7", "--file", str(jsonld_file(tmp_path)))

    assert result.exit_code == 0, result.output
    assert "POST /projects/7/iterations/upload-jsonld" in publisher.paths()
    assert "Run validation when you have added everything." in result.output


def test_add_refuses_csv_files_and_a_template_for_a_json_ld_project(
    cli: CliRunner, publisher: FakePublisher, tmp_path: Path
) -> None:
    publisher.project["projectType"] = "ApiPublishing"

    csv_result = run(cli, "project", "add", "--project-id", "7", "--file", str(csv_file(tmp_path)))
    type_result = run(
        cli, "project", "add", "--project-id", "7", "--file", str(jsonld_file(tmp_path)), "--type", "credentials"
    )

    assert "is not a .json or .jsonld file" in csv_result.output
    assert "an API publishing project does not take it" in type_result.output
    assert not any(path.endswith("upload-jsonld") for path in publisher.paths())


def test_run_validation_waits_for_a_csv_project_that_has_started_validating(
    cli: CliRunner, publisher: FakePublisher
) -> None:
    result = run(cli, "project", "run", "validation", "--project-id", "7")

    assert result.exit_code == 0, result.output
    assert not any(path.endswith("/validation/start") for path in publisher.paths())
    assert "Iteration 1: 2 succeeded, 0 with errors." in result.output
    output = " ".join(result.output.split())
    assert "already ran when the files were added" in output
    assert "To validate again, add a fixed file." in output


def test_run_validation_says_a_csv_project_started_validating_when_the_files_were_added(
    cli: CliRunner, publisher: FakePublisher
) -> None:
    publisher.iterations = [{"iterationId": 1, "status": "Validating"}]

    result = run(cli, "project", "run", "validation", "--project-id", "7", "--no-wait")

    assert "started when the files were added" in " ".join(result.output.split())
    assert not any(path.endswith("/validation/start") for path in publisher.paths())


def test_run_validation_does_not_start_a_second_run_for_a_validated_json_ld_iteration(
    cli: CliRunner, publisher: FakePublisher
) -> None:
    publisher.project["projectType"] = "ApiPublishing"

    result = run(cli, "project", "run", "validation", "--project-id", "7")

    output = " ".join(result.output.split())
    assert "has already been validated" in output
    assert "To validate again, add or replace a file." in output
    assert not any(path.endswith("/validation/start") for path in publisher.paths())


def test_run_validation_starts_a_json_ld_iteration_that_has_not_started(
    cli: CliRunner, publisher: FakePublisher
) -> None:
    publisher.project["projectType"] = "ApiPublishing"
    publisher.iterations = [{"iterationId": 1, "status": "Created"}]

    def finish_after_start(request: httpx.Request) -> httpx.Response:
        response = FakePublisher.handler(publisher, request)
        if request.url.path.endswith("/validation/start"):
            publisher.iterations[0]["status"] = "Validated"
        return response

    publisher.handler = finish_after_start  # type: ignore[method-assign]

    result = run(cli, "project", "run", "validation", "--project-id", "7")

    assert "POST /projects/7/iterations/1/validation/start" in publisher.paths()
    assert "Started validation of iteration 1." in result.output
    assert "2 succeeded" in result.output


def test_run_validation_exits_1_when_it_finds_errors(cli: CliRunner, publisher: FakePublisher) -> None:
    publisher.findings = {"jobs.csv": {"CtidReference": [finding("Missing.")]}}

    result = run(cli, "project", "run", "validation", "--project-id", "7")

    assert result.exit_code == 1
    assert "1 succeeded, 1 with errors." in result.output


def test_run_validation_no_wait_returns_while_it_is_running(cli: CliRunner, publisher: FakePublisher) -> None:
    publisher.iterations = [{"iterationId": 1, "status": "Validating"}]

    result = run(cli, "project", "run", "validation", "--project-id", "7", "--no-wait")

    assert result.exit_code == 0, result.output
    assert "is being validated" in result.output


def test_run_validation_needs_files(cli: CliRunner, publisher: FakePublisher) -> None:
    publisher.iterations = []

    result = run(cli, "project", "run", "validation", "--project-id", "7")

    assert result.exit_code == 1
    assert "no files yet" in result.output


def test_show_validation_status_as_json(cli: CliRunner, publisher: FakePublisher) -> None:
    publisher.findings = {"jobs.csv": {"CtidReference": [finding()]}}

    plain = run(cli, "project", "show", "validation", "status", "--project-id", "7", "-o", "json")
    verbose = run(
        cli, "project", "show", "validation", "status", "--project-id", "7", "-o", "json", "--verbose"
    )

    summary = json.loads(plain.output)
    assert (summary["valid"], summary["withErrors"], summary["errors"]) == (1, 1, 1)
    assert "findings" not in summary
    assert json.loads(verbose.output)["findings"][0]["column"] == "Offered By"


def test_show_validation_status_verbose_lists_each_file(cli: CliRunner, publisher: FakePublisher) -> None:
    publisher.findings = {"jobs.csv": {"CtidReference": [finding("Missing.")]}}

    result = run(cli, "project", "show", "validation", "status", "--project-id", "7", "--verbose")

    assert "✗ jobs.csv" in result.output
    assert "✓ credentials.csv" in result.output
    assert "      row 3: Offered By: error: Missing." in result.output


def test_show_validation_status_says_when_validation_has_not_run(cli: CliRunner, publisher: FakePublisher) -> None:
    publisher.iterations = [{"iterationId": 1, "status": "Created"}]

    result = run(cli, "project", "show", "validation", "status", "--project-id", "7")

    assert "Validation has not been run on it yet." in result.output


def test_show_validation_errors_lists_only_blocking_findings(cli: CliRunner, publisher: FakePublisher) -> None:
    publisher.findings = {
        "jobs.csv": {"CtidReference": [finding("Missing.")], "SpellCheck": [finding("Typo.", "Name")]}
    }

    text = run(cli, "project", "show", "validation", "errors", "--project-id", "7")
    as_json = run(cli, "project", "show", "validation", "errors", "--project-id", "7", "-o", "json")

    assert "jobs.csv:3: Offered By: error: Missing." in text.output
    assert "Typo." not in text.output
    assert text.output.rstrip().endswith("1 error")
    assert [item["message"] for item in json.loads(as_json.output)] == ["Missing."]


def test_show_audit_prints_the_log_oldest_first(cli: CliRunner, publisher: FakePublisher) -> None:
    result = run(cli, "project", "show", "audit", "--project-id", "7")

    lines = [line for line in result.output.splitlines() if line.strip()]
    assert lines[0].startswith("2026-11-12 10:00:00 UTC  ProjectCreated")
    assert "IterationFilesAdded" in lines[1]


def test_show_status_as_json(cli: CliRunner, publisher: FakePublisher) -> None:
    publisher.project.update({"status": "Completed", "publishStatus": "Published"})

    result = run(cli, "project", "show", "status", "--project-id", "7", "-o", "json")

    status = json.loads(result.output)
    assert status["status"] == "Completed"
    assert status["projectType"] == "BulkUpload"
    assert status["stages"][0]["stage"] == "ChangesetGeneration"


def test_complete_walks_a_csv_project_through_to_published(cli: CliRunner, publisher: FakePublisher) -> None:
    result = run(cli, "project", "complete", "--project-id", "7")

    assert result.exit_code == 0, result.output
    assert "Transforming the CSV files of iteration 1 to JSON-LD." in result.output
    assert "Adding you as the project's reviewer" in result.output
    assert "Approving project 7." in result.output
    assert "Publishing iteration 1." in result.output
    assert "Project 7 is published." in result.output


def test_complete_exits_1_and_says_why_it_was_refused(cli: CliRunner, publisher: FakePublisher) -> None:
    publisher.findings = {"jobs.csv": {"CtidReference": [finding("Missing.")]}}

    result = run(cli, "project", "complete", "--project-id", "7")

    assert result.exit_code == 1
    assert "Validation found 1 error(s) in iteration 1" in result.output
    assert "POST /projects/7/approve" not in publisher.paths()


def test_complete_exits_1_when_publishing_fails(cli: CliRunner, publisher: FakePublisher) -> None:
    publisher.project.update({"status": "Approved", "publishStatus": "PublishFailed"})
    publisher.iterations = [{"iterationId": 1, "status": "Transformed"}]

    def keep_failed(request: httpx.Request) -> httpx.Response:
        publisher.requests.append(request)
        if request.url.path == "/projects/7":
            return httpx.Response(200, json=publisher.project)
        if request.url.path == "/projects/7/iterations":
            return httpx.Response(200, json=publisher.iterations)
        return httpx.Response(200)

    publisher.handler = keep_failed  # type: ignore[method-assign]

    result = run(cli, "project", "complete", "--project-id", "7")

    assert result.exit_code == 1
    assert "Project 7 is failed." in result.output


def test_abandon_asks_first(cli: CliRunner, publisher: FakePublisher) -> None:
    declined = run(cli, "project", "abandon", "--project-id", "7", input="n\n")
    confirmed = run(cli, "project", "abandon", "--project-id", "7", "--yes")

    assert declined.exit_code == 1
    assert confirmed.exit_code == 0
    assert publisher.paths() == ["POST /projects/7/abandon"]


def test_a_403_shows_the_reason_the_publisher_gave(cli: CliRunner, publisher: FakePublisher) -> None:
    def forbidden(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json="Only the project's author can change or complete it.")

    publisher.handler = forbidden  # type: ignore[method-assign]

    result = run(cli, "project", "run", "validation", "--project-id", "7")

    assert result.exit_code == 1
    assert "Only the project's author can change or complete it." in result.output
    assert "Publisher user role" not in result.output


def test_a_403_without_a_reason_says_the_publisher_user_role_may_be_missing(
    cli: CliRunner, publisher: FakePublisher
) -> None:
    def forbidden(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403)

    publisher.handler = forbidden  # type: ignore[method-assign]

    result = run(cli, "project", "run", "validation", "--project-id", "7")

    assert result.exit_code == 1
    assert "Your account needs the Publisher user role." in result.output


def test_a_403_from_the_publish_permission_check_is_not_blamed_on_the_author_rule(
    cli: CliRunner, publisher: FakePublisher
) -> None:
    reason = "Cannot check who may publish these resources, because they name no owner (ceterms:ownedBy): ce-1."

    def refused(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/publish/start"):
            return httpx.Response(403, json=reason)
        return FakePublisher.handler(publisher, request)

    publisher.handler = refused  # type: ignore[method-assign]
    publisher.project["status"] = "Approved"

    result = run(cli, "project", "complete", "--project-id", "7")

    assert result.exit_code == 1
    assert reason in result.output
    assert "author" not in result.output
