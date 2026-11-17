"""Unit tests for sign-in: the device flow client, token storage, renewal and the commands.

Run with:
    pytest -m unit tests/test_auth.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs

import click
import httpx2
import pytest
from click.testing import CliRunner

from ce.auth import token_manager
from ce.auth.device_flow import (
    AccessDeniedError,
    DeviceFlowError,
    KeycloakDeviceFlowClient,
    RefreshRejectedError,
    TokenExpiredError,
    create_pkce_pair,
)
from ce.commands.auth import account_show, login, logout
from ce.config import context, settings
from ce.config.context import DEFAULT_ENVIRONMENTS
from ce.config.settings import StoredTokens

pytestmark = pytest.mark.unit

DEV = DEFAULT_ENVIRONMENTS["dev"]
TOKEN_BODY = {"access_token": "access-1", "refresh_token": "refresh-1", "expires_in": 300}
DEVICE_BODY = {
    "device_code": "device-1",
    "user_code": "ABCD-EFGH",
    "verification_uri": "https://login/device",
    "verification_uri_complete": "https://login/device?user_code=ABCD-EFGH",
    "expires_in": 600,
    "interval": 5,
}


class FakeKeycloak:
    """Keycloak's device, token, revoke and userinfo endpoints in memory."""

    def __init__(self) -> None:
        self.requests: list[httpx2.Request] = []
        self.token_answers: list[httpx2.Response | Exception] = [httpx2.Response(200, json=TOKEN_BODY)]
        self.device_answer: httpx2.Response | Exception = httpx2.Response(200, json=DEVICE_BODY)
        self.revoke_answer: httpx2.Response | Exception = httpx2.Response(200)
        self.userinfo: dict[str, Any] = {"name": "Pat Tester", "email": "pat@example.org", "sub": "user-1"}

    def handler(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        path = request.url.path

        if path.endswith("/auth/device"):
            answer = self.device_answer
        elif path.endswith("/token"):
            answer = self.token_answers.pop(0) if len(self.token_answers) > 1 else self.token_answers[0]
        elif path.endswith("/revoke"):
            answer = self.revoke_answer
        elif path.endswith("/userinfo"):
            answer = httpx2.Response(200, json=self.userinfo)
        else:
            answer = httpx2.Response(404)

        if isinstance(answer, Exception):
            raise answer
        return answer

    def client(self) -> KeycloakDeviceFlowClient:
        return KeycloakDeviceFlowClient(DEV, transport=httpx2.MockTransport(self.handler))

    def forms(self, suffix: str) -> list[dict[str, str]]:
        """The form fields of every request to an endpoint."""
        return [
            {key: values[0] for key, values in parse_qs(request.content.decode()).items()}
            for request in self.requests
            if request.url.path.endswith(suffix)
        ]


def oauth_error(error: str, status: int = 400) -> httpx2.Response:
    return httpx2.Response(status, json={"error": error, "error_description": f"{error} happened"})


@pytest.fixture
def keycloak(monkeypatch: pytest.MonkeyPatch) -> FakeKeycloak:
    """A fake Keycloak that every KeycloakDeviceFlowClient talks to; polling does not sleep."""
    fake = FakeKeycloak()
    real_init = KeycloakDeviceFlowClient.__init__

    def init_with_fake_transport(self: KeycloakDeviceFlowClient, env: Any, transport: Any = None) -> None:
        real_init(self, env, transport=httpx2.MockTransport(fake.handler))

    # Authlib's OAuth2Client is itself an httpx2.Client, so the fake goes in through the constructor, not by
    # replacing httpx2.Client.
    monkeypatch.setattr(KeycloakDeviceFlowClient, "__init__", init_with_fake_transport)
    monkeypatch.setattr("ce.auth.device_flow.time.sleep", lambda _seconds: None)
    return fake


@pytest.fixture
def config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An empty config folder with 'dev' as the active environment."""
    monkeypatch.setattr(settings, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(settings, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(settings, "TOKEN_FILE", tmp_path / "tokens.json")
    monkeypatch.setattr(context, "CONFIG_FILE", tmp_path / "config.json")
    (tmp_path / "config.json").write_text(json.dumps({"current_environment": "dev", "environments": {}}))
    return tmp_path


def stored(access: str = "access-0", refresh: str | None = "refresh-0", expires_in: float = 3600) -> StoredTokens:
    return StoredTokens(access_token=access, refresh_token=refresh, expires_at=time.time() + expires_in)


# --- device flow -------------------------------------------------------------


def test_request_device_code_returns_the_codes_and_sends_a_pkce_challenge(keycloak: FakeKeycloak) -> None:
    response = keycloak.client().request_device_code()

    assert response.user_code == "ABCD-EFGH"
    assert response.verification_uri_complete == "https://login/device?user_code=ABCD-EFGH"
    form = keycloak.forms("/auth/device")[0]
    assert form["client_id"] == DEV.client_id
    assert form["code_challenge_method"] == "S256"
    assert len(form["code_challenge"]) == 43


def test_device_pkce_challenge_matches_the_verifier_sent_for_the_token(keycloak: FakeKeycloak) -> None:
    client = keycloak.client()
    device = client.request_device_code()

    client.poll_for_token(device.device_code, interval=0, expires_in=60)

    challenge = keycloak.forms("/auth/device")[0]["code_challenge"]
    verifier = keycloak.forms("/token")[0]["code_verifier"]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    assert base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii") == challenge


def test_device_pkce_is_new_for_every_request(keycloak: FakeKeycloak) -> None:
    client = keycloak.client()
    client.request_device_code()
    client.request_device_code()

    first, second = (form["code_challenge"] for form in keycloak.forms("/auth/device"))
    assert first != second
    assert create_pkce_pair()[0] != create_pkce_pair()[0]


def test_poll_refuses_a_device_code_that_is_not_the_pending_one(keycloak: FakeKeycloak) -> None:
    client = keycloak.client()
    client.request_device_code()

    with pytest.raises(DeviceFlowError, match="does not match"):
        client.poll_for_token("another-device-code", interval=0, expires_in=60)


def test_request_device_code_reports_an_http_error(keycloak: FakeKeycloak) -> None:
    keycloak.device_answer = oauth_error("invalid_client", 401)

    with pytest.raises(DeviceFlowError, match="invalid_client happened"):
        keycloak.client().request_device_code()


def test_request_device_code_wraps_a_transport_error(keycloak: FakeKeycloak) -> None:
    keycloak.device_answer = httpx2.ConnectError("connection refused")

    with pytest.raises(DeviceFlowError, match="Device authorization request failed"):
        keycloak.client().request_device_code()


def test_poll_returns_the_tokens_on_the_first_success(keycloak: FakeKeycloak) -> None:
    tokens = keycloak.client().poll_for_token("device-1", interval=0, expires_in=60)

    assert tokens.access_token == "access-1"
    assert tokens.refresh_token == "refresh-1"
    assert keycloak.forms("/token")[0]["grant_type"] == "urn:ietf:params:oauth:grant-type:device_code"


def test_poll_keeps_waiting_while_authorization_is_pending(keycloak: FakeKeycloak) -> None:
    keycloak.token_answers = [oauth_error("authorization_pending"), httpx2.Response(200, json=TOKEN_BODY)]
    pending: list[int] = []

    tokens = keycloak.client().poll_for_token(
        "device-1", interval=0, expires_in=60, on_pending=lambda: pending.append(1)
    )

    assert tokens.access_token == "access-1"
    assert len(pending) == 1


def test_poll_slows_down_when_asked(keycloak: FakeKeycloak, monkeypatch: pytest.MonkeyPatch) -> None:
    keycloak.token_answers = [oauth_error("slow_down"), httpx2.Response(200, json=TOKEN_BODY)]
    waits: list[float] = []
    monkeypatch.setattr("ce.auth.device_flow.time.sleep", waits.append)

    keycloak.client().poll_for_token("device-1", interval=5, expires_in=60)

    assert waits == [5, 10]


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        ("access_denied", AccessDeniedError),
        ("expired_token", TokenExpiredError),
        ("device_code_expired", TokenExpiredError),
        ("server_error", DeviceFlowError),
    ],
)
def test_poll_raises_for_a_final_error(keycloak: FakeKeycloak, error: str, expected: type[Exception]) -> None:
    keycloak.token_answers = [oauth_error(error)]

    with pytest.raises(expected):
        keycloak.client().poll_for_token("device-1", interval=0, expires_in=60)


def test_poll_times_out(keycloak: FakeKeycloak) -> None:
    keycloak.token_answers = [oauth_error("authorization_pending")]

    with pytest.raises(TokenExpiredError, match="Timed out"):
        keycloak.client().poll_for_token("device-1", interval=0, expires_in=0)


def test_poll_wraps_a_transport_error(keycloak: FakeKeycloak) -> None:
    keycloak.token_answers = [httpx2.ConnectError("connection refused")]

    with pytest.raises(DeviceFlowError, match="Token request failed"):
        keycloak.client().poll_for_token("device-1", interval=0, expires_in=60)


def test_poll_wraps_a_proxys_error_page(keycloak: FakeKeycloak) -> None:
    keycloak.token_answers = [httpx2.Response(502, text="<html>Bad gateway</html>")]

    with pytest.raises(DeviceFlowError, match="Token request failed.*502"):
        keycloak.client().poll_for_token("device-1", interval=0, expires_in=60)


def test_poll_wraps_an_ok_answer_that_is_not_json(keycloak: FakeKeycloak) -> None:
    keycloak.token_answers = [httpx2.Response(200, text="<html>Welcome</html>")]

    with pytest.raises(DeviceFlowError, match="was not JSON"):
        keycloak.client().poll_for_token("device-1", interval=0, expires_in=60)


def test_refresh_keeps_the_old_refresh_token_when_none_comes_back(keycloak: FakeKeycloak) -> None:
    keycloak.token_answers = [httpx2.Response(200, json={"access_token": "access-2", "expires_in": 300})]

    tokens = keycloak.client().refresh_access_token("refresh-0")

    assert (tokens.access_token, tokens.refresh_token) == ("access-2", "refresh-0")


def test_refresh_refused_by_keycloak_is_a_rejection(keycloak: FakeKeycloak) -> None:
    keycloak.token_answers = [oauth_error("invalid_grant")]

    with pytest.raises(RefreshRejectedError, match="invalid_grant happened"):
        keycloak.client().refresh_access_token("refresh-0")


@pytest.mark.parametrize(
    "answer", [httpx2.ConnectError("connection refused"), httpx2.Response(503, text="unavailable")]
)
def test_refresh_that_could_not_be_tried_is_not_a_rejection(
    keycloak: FakeKeycloak, answer: httpx2.Response | Exception
) -> None:
    keycloak.token_answers = [answer]

    with pytest.raises(DeviceFlowError) as error:
        keycloak.client().refresh_access_token("refresh-0")

    assert not isinstance(error.value, RefreshRejectedError)


def test_revoke_posts_the_token_to_the_revocation_endpoint(keycloak: FakeKeycloak) -> None:
    keycloak.client().revoke_token("refresh-0")

    assert keycloak.requests[0].url.path.endswith("/protocol/openid-connect/revoke")
    assert keycloak.forms("/revoke")[0] == {
        "client_id": DEV.client_id,
        "token": "refresh-0",
        "token_type_hint": "refresh_token",
    }


@pytest.mark.parametrize("answer", [httpx2.Response(400, json={"error": "invalid_request"}), httpx2.ConnectError("down")])
def test_revoke_reports_a_failure(keycloak: FakeKeycloak, answer: httpx2.Response | Exception) -> None:
    keycloak.revoke_answer = answer

    with pytest.raises(DeviceFlowError):
        keycloak.client().revoke_token("refresh-0")


# --- token storage -----------------------------------------------------------


def test_tokens_are_kept_per_environment(config_dir: Path) -> None:
    settings.save_tokens(stored("dev-token"), "dev")
    settings.save_tokens(stored("test-token"), "test")

    assert settings.load_tokens("dev").access_token == "dev-token"
    assert settings.load_tokens("test").access_token == "test-token"
    assert settings.load_tokens().access_token == "dev-token"
    assert settings.load_tokens("prod") is None
    assert (config_dir / "tokens-dev.json").exists()


def test_delete_tokens_removes_only_that_environment(config_dir: Path) -> None:
    settings.save_tokens(stored(), "dev")
    settings.save_tokens(stored(), "test")

    settings.delete_tokens("dev")

    assert settings.load_tokens("dev") is None
    assert settings.load_tokens("test") is not None


def test_tokens_saved_before_environments_had_their_own_file_go_to_the_active_one(config_dir: Path) -> None:
    (config_dir / "tokens.json").write_text(stored("old-token").model_dump_json())

    assert settings.load_tokens("test") is None
    assert settings.load_tokens().access_token == "old-token"
    assert not (config_dir / "tokens.json").exists()
    assert (config_dir / "tokens-dev.json").exists()


def test_token_file_name_is_safe_for_any_environment_name(config_dir: Path) -> None:
    assert settings.token_file("my env/..").name == "tokens-my_env_...json"


def test_corrupt_tokens_count_as_none(config_dir: Path) -> None:
    (config_dir / "tokens-dev.json").write_text("{ not json")

    assert settings.load_tokens("dev") is None


# --- renewal -----------------------------------------------------------------


def test_no_saved_session_is_not_logged_in(config_dir: Path, keycloak: FakeKeycloak) -> None:
    result = token_manager.resolve_access_token()

    assert (result.access_token, result.reason) == (None, token_manager.NOT_LOGGED_IN)
    assert keycloak.requests == []


def test_a_fresh_token_is_returned_without_asking_keycloak(config_dir: Path, keycloak: FakeKeycloak) -> None:
    settings.save_tokens(stored("access-0"), "dev")

    assert token_manager.get_valid_access_token() == "access-0"
    assert keycloak.requests == []


def test_an_expired_token_is_renewed_and_saved_for_its_environment(config_dir: Path, keycloak: FakeKeycloak) -> None:
    settings.save_tokens(stored(expires_in=-10), "dev")

    assert token_manager.get_valid_access_token() == "access-1"
    assert settings.load_tokens("dev").refresh_token == "refresh-1"
    assert keycloak.forms("/token")[0]["refresh_token"] == "refresh-0"


def test_force_refresh_replaces_a_token_that_has_not_expired(config_dir: Path, keycloak: FakeKeycloak) -> None:
    settings.save_tokens(stored("access-0"), "dev")

    assert token_manager.get_valid_access_token(force_refresh=True) == "access-1"


def test_a_blank_access_token_is_renewed(config_dir: Path, keycloak: FakeKeycloak) -> None:
    settings.save_tokens(stored(" "), "dev")

    assert token_manager.get_valid_access_token() == "access-1"


def test_a_refused_renewal_ends_the_saved_session(config_dir: Path, keycloak: FakeKeycloak) -> None:
    settings.save_tokens(stored(expires_in=-10), "dev")
    keycloak.token_answers = [oauth_error("invalid_grant")]

    result = token_manager.resolve_access_token()

    assert result.reason == token_manager.SESSION_EXPIRED
    assert settings.load_tokens("dev") is None


def test_a_renewal_that_could_not_reach_keycloak_keeps_the_saved_session(
    config_dir: Path, keycloak: FakeKeycloak
) -> None:
    settings.save_tokens(stored(expires_in=-10), "dev")
    keycloak.token_answers = [httpx2.ConnectError("connection refused")]

    result = token_manager.resolve_access_token()

    assert result.reason == token_manager.UNREACHABLE
    assert settings.load_tokens("dev").refresh_token == "refresh-0"


def test_an_expired_token_without_a_refresh_token_ends_the_session(config_dir: Path, keycloak: FakeKeycloak) -> None:
    settings.save_tokens(stored(refresh=None, expires_in=-10), "dev")

    assert token_manager.resolve_access_token().reason == token_manager.SESSION_EXPIRED
    assert settings.load_tokens("dev") is None


def test_a_session_for_one_environment_does_not_count_for_another(config_dir: Path, keycloak: FakeKeycloak) -> None:
    settings.save_tokens(stored(), "dev")

    assert token_manager.is_logged_in("dev")
    assert not token_manager.is_logged_in("test")
    assert not token_manager.is_logged_in("no-such-environment")


@pytest.mark.parametrize(
    ("answer", "exception", "message"),
    [
        (None, click.UsageError, "You are not logged in"),
        (oauth_error("invalid_grant"), click.UsageError, "Your session has expired"),
        (httpx2.ConnectError("connection refused"), click.ClickException, "You are still signed in"),
    ],
)
def test_require_login_says_why_there_is_no_token(
    config_dir: Path,
    keycloak: FakeKeycloak,
    answer: httpx2.Response | Exception | None,
    exception: type[click.ClickException],
    message: str,
) -> None:
    if answer is not None:
        settings.save_tokens(stored(expires_in=-10), "dev")
        keycloak.token_answers = [answer]

    with pytest.raises(exception, match=message) as error:
        token_manager.require_login()

    assert type(error.value) is exception


def test_require_login_returns_the_token(config_dir: Path, keycloak: FakeKeycloak) -> None:
    settings.save_tokens(stored("access-0"), "dev")

    assert token_manager.require_login() == "access-0"


# --- commands ----------------------------------------------------------------


def run(command: Callable[..., Any], *args: str, input: str | None = None) -> Any:
    return CliRunner().invoke(command, list(args), input=input)


def test_login_shows_the_code_and_saves_the_session(config_dir: Path, keycloak: FakeKeycloak) -> None:
    result = run(login)

    assert result.exit_code == 0, result.output
    assert "ABCD-EFGH" in result.output
    assert "Signed in as Pat Tester" in result.output
    assert settings.load_tokens("dev").access_token == "access-1"


def test_a_second_login_to_the_same_environment_skips_the_device_flow(
    config_dir: Path, keycloak: FakeKeycloak
) -> None:
    settings.save_tokens(stored(), "dev")

    result = run(login)

    assert "Already signed in to dev" in result.output
    assert keycloak.forms("/auth/device") == []


def test_login_to_another_environment_does_not_reuse_the_active_ones_session(
    config_dir: Path, keycloak: FakeKeycloak
) -> None:
    settings.save_tokens(stored("dev-token"), "dev")

    result = run(login, "--env", "test")

    assert result.exit_code == 0, result.output
    assert len(keycloak.forms("/auth/device")) == 1
    assert settings.load_tokens("test").access_token == "access-1"
    assert settings.load_tokens("dev").access_token == "dev-token"


def test_an_expired_session_permits_a_new_login(config_dir: Path, keycloak: FakeKeycloak) -> None:
    settings.save_tokens(stored(expires_in=-10), "dev")
    keycloak.token_answers = [oauth_error("invalid_grant"), httpx2.Response(200, json=TOKEN_BODY)]

    result = run(login)

    assert result.exit_code == 0, result.output
    assert len(keycloak.forms("/auth/device")) == 1
    assert settings.load_tokens("dev").access_token == "access-1"


def test_login_shows_a_device_code_error(config_dir: Path, keycloak: FakeKeycloak) -> None:
    keycloak.device_answer = httpx2.ConnectError("connection refused")

    result = run(login)

    assert result.exit_code == 1
    assert "Device authorization request failed" in result.output


def test_login_shows_a_polling_error_instead_of_a_traceback(config_dir: Path, keycloak: FakeKeycloak) -> None:
    keycloak.token_answers = [httpx2.ConnectError("connection refused")]

    result = run(login)

    assert result.exit_code == 1
    assert "Token request failed" in result.output
    assert not isinstance(result.exception, httpx2.HTTPError)
    assert settings.load_tokens("dev") is None


def test_logout_revokes_the_refresh_token_and_clears_the_session(config_dir: Path, keycloak: FakeKeycloak) -> None:
    settings.save_tokens(stored(), "dev")
    settings.save_tokens(stored(), "test")

    result = run(logout, "--yes")

    assert "Signed out successfully." in result.output
    assert keycloak.forms("/revoke")[0]["token"] == "refresh-0"
    assert settings.load_tokens("dev") is None
    assert settings.load_tokens("test") is not None


def test_logout_still_clears_the_session_when_revoking_fails(config_dir: Path, keycloak: FakeKeycloak) -> None:
    settings.save_tokens(stored(), "dev")
    keycloak.revoke_answer = httpx2.ConnectError("connection refused")

    result = run(logout, "--yes")

    assert "Warning: the session could not be ended" in result.output
    assert "Signed out successfully." in result.output
    assert len(keycloak.requests) == 1
    assert settings.load_tokens("dev") is None


def test_logout_without_a_refresh_token_does_not_call_keycloak(config_dir: Path, keycloak: FakeKeycloak) -> None:
    settings.save_tokens(stored(refresh=None), "dev")

    run(logout, "--yes")

    assert keycloak.requests == []
    assert settings.load_tokens("dev") is None


def test_logout_when_not_signed_in_says_so(config_dir: Path, keycloak: FakeKeycloak) -> None:
    result = run(logout, "--yes")

    assert "You are not currently signed in." in result.output
    assert keycloak.requests == []


def test_logout_asks_first(config_dir: Path, keycloak: FakeKeycloak) -> None:
    settings.save_tokens(stored(), "dev")

    result = run(logout, input="n\n")

    assert result.exit_code == 1
    assert settings.load_tokens("dev") is not None


def test_whoami_shows_the_signed_in_user(config_dir: Path, keycloak: FakeKeycloak) -> None:
    settings.save_tokens(stored(), "dev")

    result = run(account_show)

    assert "Pat Tester" in result.output
    assert "pat@example.org" in result.output


def test_whoami_when_signed_out_names_the_login_command_that_exists(config_dir: Path, keycloak: FakeKeycloak) -> None:
    result = run(account_show)

    assert "Not signed in" in result.output
    assert "ce login" in result.output
    assert "ce account login" not in result.output


def test_whoami_says_when_the_session_has_expired(config_dir: Path, keycloak: FakeKeycloak) -> None:
    settings.save_tokens(stored(expires_in=-10), "dev")
    keycloak.token_answers = [oauth_error("invalid_grant")]

    result = run(account_show)

    assert "Your session has expired" in result.output
    assert settings.load_tokens("dev") is None


def test_whoami_exits_1_when_keycloak_cannot_be_reached(config_dir: Path, keycloak: FakeKeycloak) -> None:
    settings.save_tokens(stored(expires_in=-10), "dev")
    keycloak.token_answers = [httpx2.ConnectError("connection refused")]

    result = run(account_show)

    assert result.exit_code == 1
    assert "You are still signed in" in result.output
    assert settings.load_tokens("dev") is not None
