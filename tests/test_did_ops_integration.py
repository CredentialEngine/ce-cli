"""
Integration tests for ce.iir.did_ops.

Configuration is loaded from .env.test (never hard-coded here).
Load the file before running, e.g.:

    export $(grep -v '^#' .env.test | xargs) && pytest -m integration -s

Or with pytest-dotenv / python-dotenv auto-loading if configured in pytest.ini:

    pytest -m integration -s

"""

from __future__ import annotations

import os

import pytest
import requests as req

from ce.iir.did_ops import (
    call_create_challenge,
    call_get_registry_resource,
    call_is_user_member,
    call_save_challenge_token,
    call_validate_did_key,
    call_validate_did_web,
    call_verify_jwt_signature,
    extract_user_id_from_token,
    sign_proof_jwt,
    verify_proof_jwt,
)

pytestmark = pytest.mark.integration

# ---------------------------------------------------------------------------
# Config — read once from the environment (populated from .env.test)
# ---------------------------------------------------------------------------

PUBLISHER_BASE = os.environ.get("CE_PUBLISHER_BASE", "").rstrip("/")

_RAW_DID_KEY = os.environ.get("CE_TEST_DID_KEY", "")
TEST_CTID    = os.environ.get("CE_TEST_CTID", "")
TEST_USER_ID = os.environ.get("CE_TEST_USER_ID", "")
TEST_DID_KEY = _RAW_DID_KEY
TEST_DID_WEB = os.environ.get("CE_TEST_DID_WEB")
TEST_ALG     = os.environ.get("CE_TEST_ALG", "Ed25519")
TEST_VM      = (
    f"{_RAW_DID_KEY}#{_RAW_DID_KEY[len('did:key:'):]}"
    if _RAW_DID_KEY.startswith("did:key:")
    else os.environ.get("CE_TEST_VM", "")
)

# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def _require_env():
    """Fail fast with a clear message when mandatory variables are missing."""
    missing = [
        name for name in (
            "CE_PUBLISHER_BASE",
            "CE_TEST_ACCESS_TOKEN",
            "CE_TEST_CTID",
            "CE_TEST_DID_KEY",
        )
        if not os.environ.get(name, "").strip()
    ]
    if missing:
        pytest.skip(
            "Missing required environment variables (load .env.test first): "
            + ", ".join(missing)
        )


@pytest.fixture(scope="session", autouse=True)
def server_available():
    """Skip everything if the API server isn't reachable."""
    try:
        req.get(f"{PUBLISHER_BASE}/api/iir/isUserAMember", timeout=5, verify=False)
    except req.exceptions.ConnectionError:
        pytest.skip(f"API server not reachable at {PUBLISHER_BASE}")


@pytest.fixture(scope="session")
def access_token() -> str:
    token = os.environ.get("CE_TEST_ACCESS_TOKEN", "").strip()
    if not token:
        pytest.skip("CE_TEST_ACCESS_TOKEN not set — skipping integration tests.")
    return token


@pytest.fixture(scope="session")
def private_key() -> str:
    key = os.environ.get("CE_TEST_PRIVKEY_MULTIBASE", "").strip()
    if not key:
        pytest.skip("CE_TEST_PRIVKEY_MULTIBASE not set — skipping crypto tests.")
    return key


@pytest.fixture(scope="session")
def user_id(access_token) -> str:
    if TEST_USER_ID:
        return TEST_USER_ID
    return extract_user_id_from_token(access_token)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestIsUserMemberIntegration:
    def test_member_check_returns_a_bool(self, access_token, user_id):
        ok, err = call_is_user_member(
            user_id, TEST_CTID, access_token, PUBLISHER_BASE, ssl_verify=False
        )
        assert isinstance(ok, bool)
        if not ok:
            assert err

    def test_member_of_known_org(self, access_token, user_id):
        ok, err = call_is_user_member(
            user_id, TEST_CTID, access_token, PUBLISHER_BASE, ssl_verify=False
        )
        assert ok, f"Expected user to be a member: {err}"

    def test_bogus_ctid_returns_error(self, access_token, user_id):
        ok, err = call_is_user_member(
            user_id, "ce-00000000-0000-0000-0000-999999999999",
            access_token, PUBLISHER_BASE, ssl_verify=False,
        )
        assert not ok


class TestGetRegistryResourceIntegration:
    def test_known_ctid_exists_in_registry(self, access_token):
        ok, data, err = call_get_registry_resource(
            TEST_CTID, access_token, PUBLISHER_BASE, ssl_verify=False
        )
        assert ok, f"Registry lookup failed: {err}"
        assert "Name" in data or "LegalName" in data

    def test_unknown_ctid_not_found(self, access_token):
        ok, data, err = call_get_registry_resource(
            "ce-00000000-0000-0000-0000-999999999999",
            access_token, PUBLISHER_BASE, ssl_verify=False,
        )
        assert not ok
        assert err


class TestValidateDidKeyIntegration:
    def test_valid_did_key_returns_vm_ids(self, access_token):
        ok, data, err = call_validate_did_key(
            TEST_DID_KEY, TEST_ALG, access_token, PUBLISHER_BASE, ssl_verify=False
        )
        assert ok, f"DID key validation failed: {err}"
        assert data

    def test_malformed_did_key_returns_error(self, access_token):
        ok, data, err = call_validate_did_key(
            "did:key:zinvalid", "Ed25519", access_token, PUBLISHER_BASE, ssl_verify=False
        )
        assert not ok


class TestValidateDidWebIntegration:
    def test_valid_did_web_resolves(self, access_token):
        ok, data, err = call_validate_did_web(
            TEST_DID_WEB, access_token, PUBLISHER_BASE, ssl_verify=False
        )
        assert ok, f"DID web validation failed: {err}"

    def test_nonexistent_domain_returns_error(self, access_token):
        ok, data, err = call_validate_did_web(
            "did:web:this-domain-does-not-exist-xyz.invalid",
            access_token, PUBLISHER_BASE, ssl_verify=False,
        )
        assert not ok


class TestFullChallengeFlowIntegration:
    def test_create_challenge(self, access_token):
        ok, challenge, err = call_create_challenge(
            TEST_CTID, TEST_VM, access_token, PUBLISHER_BASE, ssl_verify=False
        )
        assert ok, f"createChallenges failed: {err}"
        assert challenge.get("challenge") or challenge.get("Challenge")

    def test_full_sign_verify_save_flow(self, access_token, private_key):
        ok, challenge, err = call_create_challenge(
            TEST_CTID, TEST_VM, access_token, PUBLISHER_BASE, ssl_verify=False
        )
        assert ok, f"createChallenges failed: {err}"

        challenge_uuid = challenge.get("challenge") or challenge.get("Challenge", "")
        payload = {
            "did":       challenge.get("Did") or challenge.get("did", TEST_DID_KEY),
            "challenge": challenge_uuid,
            "aud":       challenge.get("Aud") or challenge.get("aud", ""),
            "iat":       challenge.get("Iat") or challenge.get("iat", 0),
            "exp":       challenge.get("Exp") or challenge.get("exp", 0),
            "ctid":      TEST_CTID,
        }

        proof_jwt = sign_proof_jwt(private_key, TEST_VM, payload)
        assert proof_jwt

        ok, err = verify_proof_jwt(proof_jwt, TEST_VM)
        assert ok, f"Local JWT verification failed: {err}"

        ok, err = call_verify_jwt_signature(
            proof_jwt, challenge_uuid, access_token, PUBLISHER_BASE, ssl_verify=False
        )
        assert ok, f"API JWT verification failed: {err}"

        ok, err = call_save_challenge_token(
            TEST_CTID, challenge_uuid, proof_jwt,
            access_token, PUBLISHER_BASE, ssl_verify=False,
        )
        assert ok, f"saveChallengeToken failed: {err}"