"""Record and replay tests for ce publisher: what a user does, recorded against a real Publisher.

Each test is a scenario a user goes through, typed as the commands they would type. The HTTP exchange is stored in
tests/cassettes/publisher (one JSON file per test) and replayed with no network and no secrets.

    # Replay (default, and what CI runs): needs nothing.
    pytest tests/test_publisher_replay.py

    # Record: needs a Publisher and a saved sign-in for it (ce login). See the README, "Tests".
    $env:CE_CLI_RECORD_CASSETTES = "true"; pytest tests/test_publisher_replay.py

A scenario whose cassette does not exist yet is skipped in replay on a developer's machine, so a new test can be merged before it
is recorded. In CI (the CI environment variable is set) it fails instead, so a deleted or renamed cassette is not silent.
Review a cassette before committing it: it holds the project names and file contents the Publisher sent. E-mail addresses and
the signed-in user's id are replaced, and the project list holds only the projects the scenario created.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from _cassette import (
    REPLAY_ACCESS_TOKEN,
    cassette_path,
    publisher_cassette,
    recording_enabled,
    report_missing_cassette,
    scenario_passed,
)
from click.testing import CliRunner

from ce.implementations.publisher import service
from ce.publisher import main as publisher_group

pytestmark = [pytest.mark.integration, pytest.mark.recorded]

# The address replay uses. Cassettes hold paths only, so recording against any address works.
REPLAYED_PUBLISHER_URL = "http://publisher.recorded.invalid"

FIXTURES = Path(__file__).parent / "fixtures" / "publisher"

def without_sleeping() -> list[tuple[dict, object]]:
    """Waiting for validation polls every few seconds; replay answers at once, so do not sleep between polls."""
    saved = []
    for function in vars(service).values():
        defaults = getattr(function, "__kwdefaults__", None)
        if defaults and "sleep" in defaults:
            saved.append((defaults, defaults["sleep"]))
            defaults["sleep"] = lambda seconds: None
    return saved


@pytest.fixture
def cli(request: pytest.FixtureRequest):
    """The commands, with every Publisher request recorded or replayed through tests/cassettes/publisher."""
    path = cassette_path(request.node.name)
    patches = []
    saved: list[tuple[dict, object]] = []
    if not recording_enabled():
        if not path.exists():
            report_missing_cassette(request.node.name)
        env = SimpleNamespace(publisher_api_base=REPLAYED_PUBLISHER_URL, ssl_verify=True)
        patches = [
            patch("ce.implementations.publisher.cli.require_environment", return_value=("replay", env)),
            patch("ce.implementations.publisher.cli.require_login", return_value=REPLAY_ACCESS_TOKEN),
        ]
        saved = without_sleeping()

    for item in patches:
        item.start()
    try:
        # A scenario that fails while recording writes no cassette (and leaves an existing one alone).
        with publisher_cassette(path, only_projects_created_here=True, keep=scenario_passed(request)):
            yield CliRunner()
    finally:
        for item in patches:
            item.stop()
        for defaults, original in saved:
            defaults["sleep"] = original


def ce(cli: CliRunner, *args: str):
    """Run `ce publisher <args>` and return the result (exit code and what was printed)."""
    result = cli.invoke(publisher_group, list(args))
    # A request that does not match the cassette raises inside the command. Show that, not just "exit code 1".
    if result.exception and not isinstance(result.exception, SystemExit):
        raise result.exception
    return result


def created_project_id(result) -> int:
    assert result.exit_code == 0, result.output
    match = re.search(r"Created project (\d+)", result.output)
    assert match, result.output
    return int(match.group(1))


def as_json(result):
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def validation_errors(cli: CliRunner, project_id: int) -> list[dict]:
    return as_json(ce(cli, "project", "validation", "errors", "show", "--project-id", str(project_id), "-o", "json"))


def test_a_bu_project_from_create_to_abandon(cli: CliRunner) -> None:
    project_id = created_project_id(ce(cli, "project", "create", "--name", "ce-cli replay: BU project"))

    listing = ce(cli, "project", "list")
    assert listing.exit_code == 0, listing.output
    assert re.search(rf"^\s*{project_id}\s+BU\s", listing.output, re.MULTILINE), listing.output

    added = ce(
        cli, "project", "add", "--project-id", str(project_id),
        "--file", str(FIXTURES / "credentials.csv"), "--type", "credentials",
    )
    assert added.exit_code == 0, added.output
    assert "Added credentials.csv" in added.output
    assert "Validation has started" in added.output

    # A BU project validates when the file is added, so `validation run` only waits for that run.
    ran = ce(cli, "project", "validation", "run", "--project-id", str(project_id))
    errors = validation_errors(cli, project_id)
    assert ran.exit_code == (1 if errors else 0), ran.output

    status = as_json(ce(cli, "project", "status", "show", "--project-id", str(project_id), "-o", "json"))
    assert status["projectId"] == project_id
    assert status["iteration"]["status"] in ("Validated", "Transformed")

    audit = as_json(ce(cli, "project", "audit", "show", "--project-id", str(project_id), "-o", "json"))
    assert audit, "the audit log should record that the project was created and a file was added"

    abandoned = ce(cli, "project", "abandon", "--project-id", str(project_id), "--yes")
    assert abandoned.exit_code == 0, abandoned.output
    assert f"Project {project_id} is abandoned." in abandoned.output


def test_a_csv_with_a_broken_structure_is_reported(cli: CliRunner) -> None:
    project_id = created_project_id(ce(cli, "project", "create", "--name", "ce-cli replay: broken CSV"))
    added = ce(
        cli, "project", "add", "--project-id", str(project_id),
        "--file", str(FIXTURES / "credentials-bad-structure.csv"), "--type", "credentials",
    )
    assert added.exit_code == 0, added.output

    ran = ce(cli, "project", "validation", "run", "--project-id", str(project_id))
    assert ran.exit_code == 1, ran.output

    errors = validation_errors(cli, project_id)
    assert errors, "a CSV with a broken structure must have at least one blocking finding"
    assert all(item["file"] == "credentials-bad-structure.csv" for item in errors)

    shown = ce(cli, "project", "validation", "errors", "show", "--project-id", str(project_id))
    assert shown.exit_code == 0, shown.output
    assert "credentials-bad-structure.csv" in shown.output

    assert ce(cli, "project", "abandon", "--project-id", str(project_id), "--yes").exit_code == 0


def test_an_api_publishing_project_validates_json_ld(cli: CliRunner) -> None:
    project_id = created_project_id(ce(cli, "project", "create", "--name", "ce-cli replay: JSON-LD", "--jsonld"))

    listing = ce(cli, "project", "list")
    assert re.search(rf"^\s*{project_id}\s+API\s", listing.output, re.MULTILINE), listing.output

    added = ce(cli, "project", "add", "--project-id", str(project_id), "--file", str(FIXTURES / "credentials.json"))
    assert added.exit_code == 0, added.output
    assert "Run validation when you have added everything." in added.output

    # An API publishing project is validated only when asked.
    ran = ce(cli, "project", "validation", "run", "--project-id", str(project_id))
    assert "Started validation" in ran.output
    errors = validation_errors(cli, project_id)
    assert ran.exit_code == (1 if errors else 0), ran.output

    status = as_json(ce(cli, "project", "status", "show", "--project-id", str(project_id), "-o", "json"))
    assert status["projectType"] == "ApiPublishing"
    assert status["iteration"]["status"] == "Validated"

    assert ce(cli, "project", "abandon", "--project-id", str(project_id), "--yes").exit_code == 0


def test_an_invalid_json_ld_file_is_reported(cli: CliRunner) -> None:
    project_id = created_project_id(ce(cli, "project", "create", "--name", "ce-cli replay: bad JSON-LD", "--jsonld"))
    added = ce(cli, "project", "add", "--project-id", str(project_id), "--file", str(FIXTURES / "bad-no-ctid.json"))
    assert added.exit_code == 0, added.output

    ran = ce(cli, "project", "validation", "run", "--project-id", str(project_id))
    assert ran.exit_code == 1, ran.output

    errors = validation_errors(cli, project_id)
    assert errors, "a resource with no CTID must have a blocking finding"
    assert all(item["file"] == "bad-no-ctid.json" for item in errors)

    assert ce(cli, "project", "abandon", "--project-id", str(project_id), "--yes").exit_code == 0


PUBLISH = FIXTURES / "publish"


def complete_and_check_published(cli: CliRunner, project_id: int, iteration: int) -> None:
    """`project complete` on a validated BU project: transform, approve, publish, and wait until it is published."""
    completed = ce(cli, "project", "complete", "--project-id", str(project_id))
    assert completed.exit_code == 0, completed.output
    assert f"Transforming the CSV files of iteration {iteration} to JSON-LD." in completed.output
    assert f"Approving project {project_id}." in completed.output
    assert f"Publishing iteration {iteration}." in completed.output
    assert f"Project {project_id} is published." in completed.output

    status = as_json(ce(cli, "project", "status", "show", "--project-id", str(project_id), "-o", "json"))
    assert status["status"] == "Completed"
    assert status["publishStatus"] == "Published"


def test_a_bu_project_publishes_a_csv(cli: CliRunner) -> None:
    project_id = created_project_id(ce(cli, "project", "create", "--name", "ce-cli replay: publish a CSV"))
    added = ce(
        cli, "project", "add", "--project-id", str(project_id),
        "--file", str(PUBLISH / "credentials.csv"), "--type", "credentials",
    )
    assert added.exit_code == 0, added.output
    assert "Added credentials.csv" in added.output

    ran = ce(cli, "project", "validation", "run", "--project-id", str(project_id))
    assert ran.exit_code == 0, ran.output
    assert validation_errors(cli, project_id) == []

    complete_and_check_published(cli, project_id, iteration=1)


def test_a_bu_project_fixes_a_broken_csv_and_publishes(cli: CliRunner) -> None:
    project_id = created_project_id(ce(cli, "project", "create", "--name", "ce-cli replay: fix a CSV and publish"))

    # The broken file and the fixed one have the same name, so adding the fixed one replaces it in a new iteration.
    broken = ce(
        cli, "project", "add", "--project-id", str(project_id),
        "--file", str(FIXTURES / "fix-and-publish" / "credentials.csv"), "--type", "credentials",
    )
    assert broken.exit_code == 0, broken.output
    assert ce(cli, "project", "validation", "run", "--project-id", str(project_id)).exit_code == 1
    errors = validation_errors(cli, project_id)
    assert errors and all(item["file"] == "credentials.csv" for item in errors)

    # A project with errors cannot be completed, and nothing is changed by trying.
    refused = ce(cli, "project", "complete", "--project-id", str(project_id))
    assert refused.exit_code == 1, refused.output
    assert "Validation found" in refused.output and "iteration 1" in refused.output

    fixed = ce(
        cli, "project", "add", "--project-id", str(project_id),
        "--file", str(PUBLISH / "credentials.csv"), "--type", "credentials",
    )
    assert fixed.exit_code == 0, fixed.output
    ran = ce(cli, "project", "validation", "run", "--project-id", str(project_id))
    assert ran.exit_code == 0, ran.output
    assert validation_errors(cli, project_id) == []

    complete_and_check_published(cli, project_id, iteration=2)


def test_a_bu_project_publishes_learning_opportunities_from_a_csv(cli: CliRunner) -> None:
    project_id = created_project_id(ce(cli, "project", "create", "--name", "ce-cli replay: publish learning opportunities"))
    added = ce(
        cli, "project", "add", "--project-id", str(project_id),
        "--file", str(PUBLISH / "learning-opportunities.csv"), "--type", "learning-opportunities",
    )
    assert added.exit_code == 0, added.output
    assert "Added learning-opportunities.csv" in added.output

    ran = ce(cli, "project", "validation", "run", "--project-id", str(project_id))
    assert ran.exit_code == 0, ran.output
    assert validation_errors(cli, project_id) == []

    complete_and_check_published(cli, project_id, iteration=1)


def test_a_csv_that_names_an_unknown_organization_is_reported(cli: CliRunner) -> None:
    project_id = created_project_id(ce(cli, "project", "create", "--name", "ce-cli replay: unknown CTID"))

    # Offered By holds a well-formed CTID that the registry does not have, so the Consumer API cannot resolve it.
    added = ce(
        cli, "project", "add", "--project-id", str(project_id),
        "--file", str(FIXTURES / "ctid-check" / "credentials.csv"), "--type", "credentials",
    )
    assert added.exit_code == 0, added.output
    ran = ce(cli, "project", "validation", "run", "--project-id", str(project_id))
    assert ran.exit_code == 1, ran.output

    findings = [item for item in validation_errors(cli, project_id) if item["type"] == "CtidReference"]
    assert findings, "a CTID the registry does not have must be reported as a CtidReference finding"
    assert all(item["file"] == "credentials.csv" and item["column"] == "Offered By" for item in findings)
    assert any("ce-5d1c7a3e-9b24-4e68-8f10-2a6c4b9d7e35" in item["value"] for item in findings)

    # A CTID finding blocks the transform, so the project cannot be completed.
    refused = ce(cli, "project", "complete", "--project-id", str(project_id))
    assert refused.exit_code == 1, refused.output
    assert "Validation found" in refused.output

    assert ce(cli, "project", "abandon", "--project-id", str(project_id), "--yes").exit_code == 0


def test_a_project_that_does_not_exist_is_refused(cli: CliRunner) -> None:
    result = ce(cli, "project", "status", "show", "--project-id", "999999")
    assert result.exit_code == 1
    assert "999999" in result.output or "404" in result.output or "403" in result.output
