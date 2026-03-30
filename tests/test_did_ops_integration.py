"""
Integration tests for ce.iir.did_ops.

Run with:
    pytest -m integration -s
"""

from __future__ import annotations

import os
import sys

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

PUBLISHER_BASE = "https://localhost:44330"

TEST_CTID    = "ce-a4041983-b1ae-4ad4-a43d-284a5b4b2d73"
TEST_USER_ID = ""  
TEST_DID_KEY = "did:key:z6MkgEaGfhgrDL3th8pZG8KZ1DPCX2YLa45GxUNbC2bBLkej"
TEST_DID_WEB = "did:web:sandbox.credentialengine.org"
TEST_ALG     = "Ed25519"
TEST_VM      = "did:key:z6MkgEaGfhgrDL3th8pZG8KZ1DPCX2YLa45GxUNbC2bBLkej#z6MkgEaGfhgrDL3th8pZG8KZ1DPCX2YLa45GxUNbC2bBLkej"




def _prompt_secret(message: str) -> str:
    """Print a prompt to stderr and read a line from the terminal directly."""
    sys.stderr.write(message)
    sys.stderr.flush()
    try:
        tty = open("CON" if sys.platform == "win32" else "/dev/tty")
        value = tty.readline().rstrip("\n")
        tty.close()
    except OSError:
        value = ""
    return value.strip()


@pytest.fixture(scope="session")
def access_token() -> str:
    """Prompt for an access token once per session.

    To skip the prompt, set CE_TEST_ACCESS_TOKEN in your environment.
    To get a token: run `ce login --env dev` then copy it from the output.
    """
    token = os.getenv("CE_TEST_ACCESS_TOKEN", "").strip()
    if token:
        return token

    sys.stderr.write(
        "\n"
        "  ┌─ Access Token Required ──────────────────────────────────────┐\n"
        "  │  Run `ce login --env dev` to log in, then paste your token.  │\n"
        "  │  The token will not be echoed or stored.                     │\n"
        "  └──────────────────────────────────────────────────────────────┘\n"
    )
    token = _prompt_secret("  Access token: ")
    if not token:
        pytest.skip("No access token provided — skipping integration tests.")
    return token


@pytest.fixture(scope="session")
def private_key() -> str:
    """Prompt for the Ed25519 private key multibase once per session.

    To skip the prompt, set CE_TEST_PRIVKEY_MULTIBASE in your environment.
    The key is never stored or logged.
    """
    key = os.getenv("CE_TEST_PRIVKEY_MULTIBASE", "").strip()
    if key:
        return key

    sys.stderr.write(
        "\n"
        "  ┌─ Private Key Required ───────────────────────────────────────┐\n"
        "  │  Enter the Ed25519 private key multibase for your DID.       │\n"
        "  │  It starts with 'z' and will not be echoed or stored.        │\n"
        "  └──────────────────────────────────────────────────────────────┘\n"
    )
    key = _prompt_secret("  Private key (z...): ")
    if not key:
        pytest.skip("No private key provided — skipping crypto tests.")
    return key


@pytest.fixture(scope="session")
def user_id(access_token) -> str:
    if TEST_USER_ID:
        return TEST_USER_ID
    return extract_user_id_from_token(access_token)


@pytest.fixture(scope="session", autouse=True)
def server_available():
    """Skip everything if the API server isn't reachable."""
    try:
        req.get(f"{PUBLISHER_BASE}/api/iir/isUserAMember", timeout=5, verify=False)
    except req.exceptions.ConnectionError:
        pytest.skip(f"API server not reachable at {PUBLISHER_BASE}")


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