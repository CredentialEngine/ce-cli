"""Record and replay the HTTP a ce command sends to the Publisher.

A test runs in one of two modes:

* Replay (the default, and what CI runs): no server and no sign-in. Each request the command makes is compared with the
  next recorded one (method, path, query and body) and answered with the recorded response.
* Record (CE_CLI_RECORD_CASSETTES=true): the command runs against a real Publisher, with the saved `ce login`. Every
  request and response is written to a JSON cassette.

httpx2 is not supported by vcrpy, so this works at the httpx2 transport level, as ceops does for its HTTP tests.
Cassettes never hold the Authorization header or the token. E-mail addresses and the signed-in user's id in responses are
replaced, and the project list is trimmed to the projects the scenario created.

To record a scenario: start a Publisher, run `ce login` for it, set CE_CLI_RECORD_CASSETTES=true and run the test. Read the new
cassette before committing it, then replay it with the variable unset. See the README, "Tests". A scenario that fails while
recording writes no cassette (`keep=scenario_passed(request)`, with the hook that tests/conftest.py registers).
"""

from __future__ import annotations

import base64
import json
import os
import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx2
import pytest

from ce.implementations.publisher.client import PublisherClient

RECORD_ENV = "CE_CLI_RECORD_CASSETTES"
CASSETTE_DIR = Path(__file__).parent / "cassettes" / "publisher"

# Where the commands build their client. The cassette replaces it so every client gets the recording or replaying transport.
CLIENT_TARGET = "ce.implementations.publisher.cli.PublisherClient"

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
JWT = re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]*")
# The word "bearer" followed by a long token. A project that is merely named "test bearer token" is not a credential.
BEARER_CREDENTIAL = re.compile(r"bearer\s+[A-Za-z0-9._~+/=-]{20,}", re.IGNORECASE)
FILENAME = re.compile(rb'filename="([^"]*)"')
PLACEHOLDER_EMAIL = "user@example.invalid"
PLACEHOLDER_USER_ID = "11111111-1111-1111-1111-111111111111"


def _b64(claims: dict[str, str]) -> str:
    return base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")


# What replay signs in with. `ce publisher project complete` reads the user id from the token and sends it (to add the user
# as reviewer), so replay needs a token that carries the placeholder id the recording was made with. It is not a real token.
REPLAY_ACCESS_TOKEN = f"{_b64({'alg': 'none'})}.{_b64({'sub': PLACEHOLDER_USER_ID})}.replay"


def recording_enabled() -> bool:
    return os.getenv(RECORD_ENV, "").lower() in {"1", "true", "yes", "record"}


def cassette_path(name: str) -> Path:
    return CASSETTE_DIR / f"{name}.json"


def describe_request(request: httpx2.Request, body: bytes, user_id: str | None = None) -> dict[str, Any]:
    """What identifies a request in a cassette: method, path, query and the body (JSON, or the uploaded file names).

    When recording, `user_id` (the signed-in user) is replaced by the placeholder, as in responses: a request can carry it,
    for example the reviewer a BU project adds when it is completed.
    """
    described: dict[str, Any] = {
        "method": request.method,
        "path": request.url.path,
        "query": request.url.query.decode("ascii"),
    }
    content_type = request.headers.get("content-type", "")
    if body and content_type.startswith("application/json"):
        described["json"] = json.loads(body)
    elif body and content_type.startswith("multipart/form-data"):
        # The boundary is random, so only the file names are compared.
        described["files"] = [name.decode("utf-8") for name in FILENAME.findall(body)]
    if user_id:
        described = json.loads(json.dumps(described).replace(user_id, PLACEHOLDER_USER_ID))
    return described


def user_id_of(access_token: str) -> str | None:
    """The signed-in user's id (the `sub` claim), or None when the token is not a readable JWT."""
    try:
        payload = access_token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    except (IndexError, ValueError):
        return None
    subject = claims.get("sub")
    return subject if isinstance(subject, str) and subject else None


def keep_only_projects(text: str, project_ids: set[int]) -> str:
    """`GET /projects` lists every project the user can see. Keep only the ones this recording created."""
    try:
        projects = json.loads(text)
    except ValueError:
        return text
    if not isinstance(projects, list):
        return text
    kept = [p for p in projects if isinstance(p, dict) and p.get("projectId") in project_ids]
    return json.dumps(kept, separators=(",", ":"), ensure_ascii=False)


def created_project_id(text: str) -> int | None:
    """The id in the answer to `POST /projects` (`{"projectId": 7}`), or None."""
    try:
        created = json.loads(text)
    except ValueError:
        return None
    project_id = created.get("projectId") if isinstance(created, dict) else None
    return project_id if isinstance(project_id, int) else None


def describe_response(
    response: httpx2.Response,
    *,
    user_id: str | None = None,
    keep_project_ids: set[int] | None = None,
    is_project_list: bool = False,
) -> dict[str, Any]:
    text = response.content.decode("utf-8")
    if keep_project_ids is not None and is_project_list:
        text = keep_only_projects(text, keep_project_ids)
    if user_id:
        text = text.replace(user_id, PLACEHOLDER_USER_ID)
    text = EMAIL.sub(PLACEHOLDER_EMAIL, text)
    return {
        "status": response.status_code,
        "content_type": response.headers.get("content-type", ""),
        "body": text,
    }


def requests_differ(expected: dict[str, Any], actual: dict[str, Any]) -> str | None:
    """A sentence saying how the request differs from the recorded one, or None if it matches."""
    for key in ("method", "path", "query", "json", "files"):
        if expected.get(key) != actual.get(key):
            return f"{key}: recorded {expected.get(key)!r}, sent {actual.get(key)!r}"
    return None


class RecordingTransport(httpx2.BaseTransport):
    """Sends the request for real, keeps the exchange, and hands the response on."""

    def __init__(
        self,
        inner: httpx2.BaseTransport,
        interactions: list[dict[str, Any]],
        *,
        user_id: str | None = None,
        created_projects: set[int] | None = None,
    ) -> None:
        self._inner = inner
        self._interactions = interactions
        self._user_id = user_id
        # None: the project list is recorded as it is. A set: the list is trimmed to these ids, which are added as projects
        # are created. Every command builds its own client and transport, so the recording shares one set between them.
        self._created = created_projects

    def handle_request(self, request: httpx2.Request) -> httpx2.Response:
        body = request.read()
        response = self._inner.handle_request(request)
        response.read()
        if self._created is not None and request.method == "POST" and request.url.path == "/projects":
            new_id = created_project_id(response.content.decode("utf-8"))
            if new_id is not None:
                self._created.add(new_id)
        described = describe_response(
            response,
            user_id=self._user_id,
            keep_project_ids=self._created,
            is_project_list=request.method == "GET" and request.url.path == "/projects",
        )
        self._interactions.append(
            {"request": describe_request(request, body, user_id=self._user_id), "response": described}
        )
        # Rebuilt without the encoding headers: the content is already decoded.
        headers = [("content-type", response.headers.get("content-type", ""))]
        return httpx2.Response(response.status_code, headers=headers, content=response.content, request=request)

    def close(self) -> None:
        self._inner.close()


class ReplayTransport(httpx2.BaseTransport):
    """Answers each request from the next recorded interaction, and notes any request that does not match."""

    def __init__(self, interactions: list[dict[str, Any]]) -> None:
        self._pending = list(interactions)
        self.problems: list[str] = []

    @property
    def unused(self) -> int:
        return len(self._pending)

    def handle_request(self, request: httpx2.Request) -> httpx2.Response:
        actual = describe_request(request, request.read())
        label = f"{actual['method']} {actual['path']}"
        if not self._pending:
            self.problems.append(f"{label}: the cassette has no more recorded requests")
            raise AssertionError(self.problems[-1])
        entry = self._pending.pop(0)
        difference = requests_differ(entry["request"], actual)
        if difference:
            self.problems.append(f"{label}: {difference}")
            raise AssertionError(self.problems[-1])
        recorded = entry["response"]
        headers = [("content-type", recorded["content_type"])] if recorded["content_type"] else []
        return httpx2.Response(
            recorded["status"], headers=headers, content=recorded["body"].encode("utf-8"), request=request
        )


def check_cassette_is_clean(text: str, token: str | None, user_id: str | None = None) -> None:
    """Refuse to keep a cassette that holds a credential or the signed-in user's id."""
    lowered = text.lower()
    assert "authorization" not in lowered, "the cassette holds an Authorization header"
    assert not BEARER_CREDENTIAL.search(text), "the cassette holds a bearer token"
    assert not JWT.search(text), "the cassette holds something shaped like a JWT"
    if token:
        assert token not in text, "the cassette holds the access token"
    if user_id:
        assert user_id not in text, "the cassette holds the signed-in user's id"


def remember_outcome(item: pytest.Item, report: pytest.TestReport) -> None:
    """Keep each phase's report on the test item, so a fixture can tell at teardown whether the test passed.

    Called by the `pytest_runtest_makereport` hook in tests/conftest.py. A fixture's teardown does not see the test's failure,
    so without this a scenario that failed half way would still be written to a cassette.
    """
    setattr(item, f"rep_{report.when}", report)


def scenario_passed(request: pytest.FixtureRequest) -> Callable[[], bool]:
    """For `publisher_cassette(keep=...)`: true only once the test body has run and passed."""

    def passed() -> bool:
        report = getattr(request.node, "rep_call", None)
        return report is not None and report.passed

    return passed


@contextmanager
def publisher_cassette(
    path: Path, *, only_projects_created_here: bool = False, keep: Callable[[], bool] | None = None
) -> Iterator[None]:
    """Record or replay every Publisher request the commands make inside the block.

    When recording, `only_projects_created_here` trims the project list (`GET /projects`) to the projects this recording
    created, so a cassette never holds the names of the other projects the signed-in user has. `keep`, asked once the block
    has ended, says whether the recording is worth keeping: when it answers false (the scenario failed) nothing is written
    and a cassette already on disk is left as it was.
    """
    if recording_enabled():
        interactions: list[dict[str, Any]] = []
        tokens: list[str] = []
        created_projects: set[int] | None = set() if only_projects_created_here else None

        def build_recording(base_url: str, access_token: str, **options: Any) -> PublisherClient:
            tokens.append(access_token)
            inner = httpx2.HTTPTransport(verify=options.get("verify", True))
            options["transport"] = RecordingTransport(
                inner,
                interactions,
                user_id=user_id_of(access_token),
                created_projects=created_projects,
            )
            return PublisherClient(base_url, access_token, **options)

        with patch(CLIENT_TARGET, side_effect=build_recording):
            yield

        if keep is not None and not keep():
            return
        assert interactions, f"nothing was recorded into {path}"
        text = json.dumps({"interactions": interactions}, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        first_token = tokens[0] if tokens else None
        check_cassette_is_clean(text, first_token, user_id_of(first_token) if first_token else None)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        return

    # utf-8-sig: PowerShell 5 writes a byte order mark when a cassette is edited by hand.
    interactions = json.loads(path.read_text(encoding="utf-8-sig"))["interactions"]
    transport = ReplayTransport(interactions)

    def build_replay(base_url: str, access_token: str, **options: Any) -> PublisherClient:
        options["transport"] = transport
        return PublisherClient(base_url, access_token, **options)

    with patch(CLIENT_TARGET, side_effect=build_replay):
        yield

    assert not transport.problems, "requests that do not match the cassette:\n" + "\n".join(transport.problems)
    assert transport.unused == 0, (
        f"{transport.unused} recorded request(s) were not made: the command now sends fewer requests than were recorded"
    )


def cassette_exists(name: str) -> bool:
    return cassette_path(name).exists()


def report_missing_cassette(name: str) -> None:
    """A scenario with no cassette skips on a developer's machine, so a new test can be merged before it is recorded.

    In CI (the `CI` environment variable, which GitHub Actions sets) it fails: a deleted or renamed cassette must not leave a
    scenario silently untested.
    """
    message = f"No cassette for {name}. Record it: see the README, 'Tests'."
    if os.getenv("CI"):
        pytest.fail(message, pytrace=False)
    pytest.skip(message)
