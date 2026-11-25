"""Tests of the record and replay helper itself (tests/_cassette.py), against a throwaway local server.

The helper is what makes tests/test_publisher_replay.py possible, so it is tested on its own: a real recording
against a real socket, then a replay with the server stopped.

Run with:
    pytest -m unit tests/test_cassette.py
"""

from __future__ import annotations

import base64
import codecs
import json
import os
import subprocess
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import _cassette
import httpx2
import pytest
from _cassette import (
    PLACEHOLDER_EMAIL,
    PLACEHOLDER_USER_ID,
    RECORD_ENV,
    REPLAY_ACCESS_TOKEN,
    check_cassette_is_clean,
    describe_request,
    publisher_cassette,
)
from click.testing import CliRunner

from ce.implementations.publisher import service
from ce.publisher import main as publisher_group

pytestmark = pytest.mark.unit

def b64(value: dict[str, str]) -> str:
    return base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip("=")


# A token shaped like a real one (the user id is its `sub`), so the clean check has something to find if it leaked.
USER_ID = "22222222-2222-2222-2222-222222222222"
TOKEN = f"{b64({'alg': 'none'})}.{b64({'sub': USER_ID})}.signature-of-the-token"
PROJECT = {
    "projectId": 7,
    "name": "Welding",
    "projectType": "BulkUpload",
    "status": "Active",
    "publishStatus": "NotPublished",
    "createdBy": "someone@example.org",
    "authorId": USER_ID,
}
# Another project of the signed-in user, which a scenario did not create.
OTHER_PROJECT = {**PROJECT, "projectId": 8, "name": "test bearer token", "createdBy": "other@example.org"}


class ThrowawayPublisher(BaseHTTPRequestHandler):
    """Two routes, enough for `project list` and `project create`."""

    def _send(self, status: int, payload: Any) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - the name http.server looks for
        self._send(200, [PROJECT, OTHER_PROJECT]) if self.path == "/projects" else self._send(404, {"title": "Not Found"})

    def do_POST(self) -> None:  # noqa: N802
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self._send(200, {"projectId": 7})

    def log_message(self, *_args: object) -> None:
        return


@contextmanager
def throwaway_server() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), ThrowawayPublisher)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()


@contextmanager
def signed_in(base_url: str) -> Iterator[None]:
    env = SimpleNamespace(publisher_api_base=base_url, ssl_verify=True)
    with patch("ce.implementations.publisher.cli.require_login", return_value=TOKEN), \
            patch("ce.implementations.publisher.cli.require_environment", return_value=("test", env)):
        yield


def run(*args: str):
    result = CliRunner().invoke(publisher_group, list(args))
    if result.exception and not isinstance(result.exception, SystemExit):
        raise result.exception
    return result


def record(path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Record `project list` and `project create` against the throwaway server; return what list printed."""
    monkeypatch.setenv(RECORD_ENV, "true")
    with throwaway_server() as url, signed_in(url), publisher_cassette(path):
        listed = run("project", "list")
        created = run("project", "create", "--name", "Welding")
    assert listed.exit_code == 0 and created.exit_code == 0, listed.output + created.output
    monkeypatch.delenv(RECORD_ENV)
    return listed.output


def test_a_missing_cassette_skips_on_a_developer_machine_and_fails_in_ci(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CI", raising=False)
    with pytest.raises(pytest.skip.Exception, match="No cassette for test_x"):
        _cassette.report_missing_cassette("test_x")

    monkeypatch.setenv("CI", "true")
    with pytest.raises(pytest.fail.Exception, match="No cassette for test_x"):
        _cassette.report_missing_cassette("test_x")


def test_a_recording_that_is_not_kept_writes_no_cassette(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "scenario.json"
    monkeypatch.setenv(RECORD_ENV, "true")
    with throwaway_server() as url, signed_in(url), publisher_cassette(path, keep=lambda: False):
        assert run("project", "list").exit_code == 0

    assert not path.exists()


def test_a_recording_that_is_not_kept_leaves_the_existing_cassette_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "scenario.json"
    record(path, monkeypatch)
    recorded = path.read_bytes()

    monkeypatch.setenv(RECORD_ENV, "true")
    with throwaway_server() as url, signed_in(url), publisher_cassette(path, keep=lambda: False):
        assert run("project", "list").exit_code == 0

    assert path.read_bytes() == recorded


def test_the_conftest_registers_the_hook_that_tells_a_fixture_whether_the_test_passed(
    request: pytest.FixtureRequest,
) -> None:
    hooks = request.config.pluginmanager.hook.pytest_runtest_makereport.get_hookimpls()

    assert any(Path(str(hook.plugin_name)).name == "conftest.py" for hook in hooks)


def test_only_a_scenario_that_passed_is_written_to_a_cassette(tmp_path: Path) -> None:
    """A failing test's fixture must not write its cassette, shown in a nested pytest run with the same hook.

    A fixture's teardown does not see the test's failure, so this fails if `scenario_passed` does not read what
    `_cassette.remember_outcome` stores. That tests/conftest.py registers the hook that calls it is the test above.
    """
    nested = tmp_path / "nested"
    cassettes = tmp_path / "cassettes"
    nested.mkdir()
    cassettes.mkdir()
    (nested / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (nested / "conftest.py").write_text(
        "import pytest\n"
        "from _cassette import remember_outcome\n"
        "\n"
        "@pytest.hookimpl(wrapper=True)\n"
        "def pytest_runtest_makereport(item, call):\n"
        "    report = yield\n"
        "    remember_outcome(item, report)\n"
        "    return report\n",
        encoding="utf-8",
    )
    (nested / "test_nested.py").write_text(
        "import os\n"
        "from pathlib import Path\n"
        "import pytest\n"
        "from _cassette import publisher_cassette, scenario_passed\n"
        "from test_cassette import run, signed_in, throwaway_server\n"
        "\n"
        "@pytest.fixture\n"
        "def scenario(request):\n"
        "    path = Path(os.environ['NESTED_CASSETTES']) / f'{request.node.name}.json'\n"
        "    with throwaway_server() as url, signed_in(url), publisher_cassette(path, keep=scenario_passed(request)):\n"
        "        yield\n"
        "\n"
        "def test_passes(scenario):\n"
        "    assert run('project', 'list').exit_code == 0\n"
        "\n"
        "def test_fails_after_the_command_ran(scenario):\n"
        "    assert run('project', 'list').exit_code == 0\n"
        "    raise AssertionError('the scenario fails')\n",
        encoding="utf-8",
    )
    env = {
        **os.environ,
        RECORD_ENV: "true",
        "NESTED_CASSETTES": str(cassettes),
        "PYTHONPATH": str(Path(__file__).parent),
    }

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "-c", str(nested / "pytest.ini")],
        cwd=nested, env=env, capture_output=True, text=True, check=False,
    )

    assert "1 failed, 1 passed" in result.stdout, result.stdout + result.stderr
    assert [item.name for item in cassettes.iterdir()] == ["test_passes.json"]


def test_a_recording_replays_with_no_server(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "scenario.json"
    printed = record(path, monkeypatch)

    # No server is running now, and the address is different: the cassette holds paths only.
    with signed_in("http://publisher.recorded.invalid"), publisher_cassette(path):
        listed = run("project", "list")
        created = run("project", "create", "--name", "Welding")

    assert listed.exit_code == 0 and created.exit_code == 0
    assert listed.output == printed
    assert "Created project 7" in created.output


def test_a_cassette_edited_in_powershell_still_replays(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "scenario.json"
    record(path, monkeypatch)
    # Windows PowerShell 5 saves edited files with a byte order mark.
    path.write_bytes(codecs.BOM_UTF8 + path.read_bytes())

    with signed_in("http://publisher.recorded.invalid"), publisher_cassette(path):
        assert run("project", "list").exit_code == 0
        assert run("project", "create", "--name", "Welding").exit_code == 0


def test_the_cassette_holds_the_exchange_and_no_credentials(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "scenario.json"
    record(path, monkeypatch)

    text = path.read_text(encoding="utf-8")
    interactions = json.loads(text)["interactions"]

    assert [(i["request"]["method"], i["request"]["path"]) for i in interactions] == [
        ("GET", "/projects"),
        ("POST", "/projects"),
    ]
    assert interactions[1]["request"]["json"]["name"] == "Welding"
    assert interactions[0]["response"]["status"] == 200
    assert TOKEN not in text and "uthorization" not in text
    assert "someone@example.org" not in text and PLACEHOLDER_EMAIL in text


def test_recording_trims_the_project_list_and_hides_the_user_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "scenario.json"
    monkeypatch.setenv(RECORD_ENV, "true")
    with throwaway_server() as url, signed_in(url), publisher_cassette(path, only_projects_created_here=True):
        assert run("project", "create", "--name", "Welding").exit_code == 0
        assert run("project", "list").exit_code == 0

    text = path.read_text(encoding="utf-8")
    listed = json.loads(json.loads(text)["interactions"][1]["response"]["body"])

    # The throwaway server answers every create with project 7; the list holds 7 and 8, and only 7 was created here.
    assert [project["projectId"] for project in listed] == [7]
    assert "test bearer token" not in text and "other@example.org" not in text
    assert USER_ID not in text and PLACEHOLDER_USER_ID in text


def test_a_command_that_sends_another_request_fails_the_replay(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "scenario.json"
    record(path, monkeypatch)

    with pytest.raises(AssertionError, match="path: recorded '/projects', sent '/projects/7'"):
        with signed_in("http://publisher.recorded.invalid"), publisher_cassette(path):
            run("project", "status", "show", "--project-id", "7")


def test_a_changed_request_body_fails_the_replay(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "scenario.json"
    record(path, monkeypatch)

    with pytest.raises(AssertionError, match="json: recorded"):
        with signed_in("http://publisher.recorded.invalid"), publisher_cassette(path):
            run("project", "list")
            run("project", "create", "--name", "Brazing")


def test_a_command_that_sends_fewer_requests_fails_the_replay(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "scenario.json"
    record(path, monkeypatch)

    with pytest.raises(AssertionError, match="1 recorded request"):
        with signed_in("http://publisher.recorded.invalid"), publisher_cassette(path):
            run("project", "list")


def test_a_command_that_sends_more_requests_fails_the_replay(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "scenario.json"
    record(path, monkeypatch)

    with pytest.raises(AssertionError, match="no more recorded requests"):
        with signed_in("http://publisher.recorded.invalid"), publisher_cassette(path):
            run("project", "list")
            run("project", "create", "--name", "Welding")
            run("project", "list")


@pytest.mark.parametrize(
    "leak",
    [
        "Authorization: Bearer abc",
        f"token {TOKEN}",
        "Bearer " + "a" * 30,
    ],
)
def test_a_cassette_with_a_credential_is_refused(leak: str) -> None:
    with pytest.raises(AssertionError):
        check_cassette_is_clean(leak, TOKEN)


def test_a_project_named_bearer_token_is_not_a_credential() -> None:
    check_cassette_is_clean('{"name":"test bearer token 2"}', TOKEN)


def test_a_cassette_with_the_user_id_is_refused() -> None:
    with pytest.raises(AssertionError, match="user's id"):
        check_cassette_is_clean(f'{{"authorId":"{USER_ID}"}}', TOKEN, USER_ID)


def test_a_request_that_carries_the_user_id_is_recorded_with_the_placeholder() -> None:
    request = httpx2.Request("POST", "http://publisher/projects/7/reviewers", json={"userId": USER_ID})

    described = describe_request(request, request.read(), user_id=USER_ID)

    assert described["json"] == {"userId": PLACEHOLDER_USER_ID}
    assert USER_ID not in json.dumps(described)


def test_the_replay_token_carries_the_placeholder_user_id() -> None:
    # `project complete` reads the user id from the token, so replay needs one it can read.
    assert service.user_id_from_token(REPLAY_ACCESS_TOKEN) == PLACEHOLDER_USER_ID


def test_the_access_token_itself_is_refused() -> None:
    with pytest.raises(AssertionError, match="access token"):
        check_cassette_is_clean("plain-secret-value", "plain-secret-value")
