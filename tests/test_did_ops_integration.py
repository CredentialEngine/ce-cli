"""
Integration tests for ce.iir.did_ops.

Config comes from .env.test — nothing is hard-coded in this file. Load it
before running, e.g. `set -a && source .env.test && set +a`, or rely on
python-dotenv (it's loaded below if available).

Two ways to run:

    # Live: hits the real publisher. Use this to (re-)record cassettes.
    VCR_RECORD_MODE=once pytest -m integration -s

    # Playback (default): replays cassettes, no network, no secrets needed.
    pytest -m integration -s
"""

from __future__ import annotations

import os

import pytest
import requests as req

# Best-effort .env.test loading. If python-dotenv isn't installed we just
# fall back to whatever's already in os.environ.
try:
    from dotenv import load_dotenv

    load_dotenv(".env.test")
except ImportError:
    pass

from ce.iir.did_ops import (
    call_create_challenges,
    call_get_organization_iir_detail,
    call_get_registry_resource,
    call_is_user_member,
    call_save_challenge_token,
    call_submit_to_iir,
    call_validate_did,
    call_validate_did_key,
    call_validate_did_web,
    call_verify_jwt_signature,
    extract_user_id_from_token,
    merge_autofill,
    sign_proof_jwt,
    verify_proof_jwt,
)

pytestmark = [pytest.mark.integration, pytest.mark.vcr]

# ---------------------------------------------------------------------------
# Environment / config
# ---------------------------------------------------------------------------

VCR_RECORD_MODE = os.environ.get("VCR_RECORD_MODE", "none").lower()
PLAYBACK_ONLY = VCR_RECORD_MODE == "none"


PUBLISHER_BASE = os.environ.get("CE_PUBLISHER_BASE", "").rstrip("/")
TEST_CTID = os.environ.get("CE_TEST_CTID", "")
TEST_DID_KEY = os.environ.get("CE_TEST_DID_KEY", "")
TEST_DID_WEB = os.environ.get("CE_TEST_DID_WEB", "")
TEST_VM = os.environ.get("CE_TEST_VM", f"{TEST_DID_KEY}#{TEST_DID_KEY.split(':')[-1]}")
TEST_ALG = os.environ.get("CE_TEST_ALG", "Ed25519")
TEST_USER_ID = os.environ.get("CE_TEST_USER_ID", "").strip()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def _require_env():
    """Bail out early — with a useful message — if live mode is missing config."""
    if PLAYBACK_ONLY:
        return

    required = ("CE_PUBLISHER_BASE", "CE_TEST_ACCESS_TOKEN", "CE_TEST_CTID", "CE_TEST_DID_KEY")
    missing = [name for name in required if not os.environ.get(name, "").strip()]
    if missing:
        pytest.skip(
            "Missing required environment variables (load .env.test first): "
            + ", ".join(missing)
        )


@pytest.fixture(scope="session", autouse=True)
def server_available():
    """In live/record mode, skip everything if the publisher isn't up."""
    if PLAYBACK_ONLY:
        return
    try:
        req.get(f"{PUBLISHER_BASE}/api/iir", timeout=5, verify=False)
    except (req.exceptions.ConnectionError, req.exceptions.Timeout):
        pytest.skip(f"API server not reachable at {PUBLISHER_BASE}")


@pytest.fixture(scope="session")
def access_token() -> str:
    if PLAYBACK_ONLY:
        return "PLAYBACK_TOKEN"
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
    # Explicit override wins, then playback dummy, then decode the live token.
    if TEST_USER_ID:
        return TEST_USER_ID
    if PLAYBACK_ONLY:
        return "00000000-0000-0000-0000-000000000000"
    return extract_user_id_from_token(access_token)


@pytest.fixture(scope="module")
def vcr_cassette_dir(request):
    """Cassettes sit next to this file in ./cassettes/."""
    return os.path.join(os.path.dirname(request.module.__file__), "cassettes")


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
            user_id,
            "ce-00000000-0000-0000-0000-999999999999",
            access_token,
            PUBLISHER_BASE,
            ssl_verify=False,
        )
        assert not ok


class TestGetRegistryResourceIntegration:
    def test_known_ctid_exists_in_registry(self, access_token):
        ok, data, err = call_get_registry_resource(
            TEST_CTID, access_token, PUBLISHER_BASE, ssl_verify=False
        )
        assert ok, f"Registry lookup failed: {err}"
        # Either field is fine — different orgs publish different shapes.
        assert "Name" in data or "LegalName" in data

    def test_unknown_ctid_not_found(self, access_token):
        ok, _data, err = call_get_registry_resource(
            "ce-00000000-0000-0000-0000-999999999999",
            access_token,
            PUBLISHER_BASE,
            ssl_verify=False,
        )
        assert not ok
        assert err


class TestGetOrganizationIIRDetailIntegration:
    def test_known_ctid_returns_org_detail_or_skips(self, access_token):
        ok, data, err = call_get_organization_iir_detail(
            TEST_CTID, access_token, PUBLISHER_BASE, ssl_verify=False
        )
        if not ok:
            pytest.skip(f"Org has no Accounts detail yet: {err}")

        assert data.get("LegalName") or data.get("LogoUrl"), (
            "getOrganizationIIRDetail returned valid=true but data was empty"
        )

    def test_unknown_ctid_returns_failure(self, access_token):
        ok, _data, err = call_get_organization_iir_detail(
            "ce-00000000-0000-0000-0000-999999999999",
            access_token,
            PUBLISHER_BASE,
            ssl_verify=False,
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
        ok, _data, _err = call_validate_did_key(
            "did:key:zinvalid", "Ed25519", access_token, PUBLISHER_BASE, ssl_verify=False
        )
        assert not ok


class TestValidateDidWebIntegration:
    def test_valid_did_web_resolves(self, access_token):
        if not TEST_DID_WEB:
            pytest.skip("CE_TEST_DID_WEB not set — skipping did:web integration test.")
        ok, _data, err = call_validate_did_web(
            TEST_DID_WEB, access_token, PUBLISHER_BASE, ssl_verify=False
        )
        assert ok, f"DID web validation failed: {err}"

    def test_nonexistent_domain_returns_error(self, access_token):
        ok, _data, _err = call_validate_did_web(
            "did:web:this-domain-does-not-exist-xyz.invalid",
            access_token,
            PUBLISHER_BASE,
            ssl_verify=False,
        )
        assert not ok


class TestFullChallengeFlowIntegration:
    def test_create_challenge(self, access_token):
        ok, challenges, err = call_create_challenges(
            TEST_CTID, [TEST_VM], access_token, PUBLISHER_BASE, ssl_verify=False
        )
        assert ok, f"createChallenges failed: {err}"
        assert isinstance(challenges, list) and challenges

        first = challenges[0]
        # The publisher has used both casings over time.
        assert first.get("Challenge") or first.get("challenge")

    def test_full_sign_verify_save_flow(self, access_token, private_key):
        ok, challenges, err = call_create_challenges(
            TEST_CTID, [TEST_VM], access_token, PUBLISHER_BASE, ssl_verify=False
        )
        assert ok, f"createChallenges failed: {err}"
        assert challenges, "createChallenges returned empty list"

        # Pick the challenge that matches our VM, otherwise fall back to first.
        challenge = next(
            (c for c in challenges if (c.get("Did") or c.get("did")) == TEST_VM),
            challenges[0],
        )

        challenge_uuid = challenge.get("Challenge") or challenge.get("challenge", "")
        assert challenge_uuid, "Challenge UUID missing from response"

        payload = {
            "did": challenge.get("Did") or challenge.get("did", TEST_DID_KEY),
            "challenge": challenge_uuid,
            "aud": challenge.get("Aud") or challenge.get("aud", ""),
            "iat": challenge.get("Iat") or challenge.get("iat", 0),
            "exp": challenge.get("Exp") or challenge.get("exp", 0),
            "ctid": TEST_CTID,
        }

        proof_jwt = sign_proof_jwt(private_key, TEST_VM, payload)
        assert proof_jwt

        # Verify locally first — cheap sanity check before hitting the API.
        ok, err = verify_proof_jwt(proof_jwt, TEST_VM)
        assert ok, f"Local JWT verification failed: {err}"

        ok, err = call_verify_jwt_signature(
            proof_jwt, challenge_uuid, access_token, PUBLISHER_BASE, ssl_verify=False
        )
        assert ok, f"API JWT verification failed: {err}"

        ok, err = call_save_challenge_token(
            TEST_CTID,
            challenge_uuid,
            proof_jwt,
            access_token,
            PUBLISHER_BASE,
            ssl_verify=False,
        )
        assert ok, f"saveChallengeToken failed: {err}"


class TestSubmitToIirIntegration:
    def test_submit_returns_success_or_already_exists(self, access_token):
        # On a fresh registry the submit succeeds; on a re-run it comes back
        # as "Did already exists". Either is fine for this test.
        ok, err = call_submit_to_iir(
            TEST_CTID,
            TEST_DID_KEY,
            "Acme Test",
            "Acme Test Corp",
            "https://registry.example.com",
            "https://acme.example.com",
            access_token,
            PUBLISHER_BASE,
            ssl_verify=False,
        )
        if not ok:
            assert err == "Did already exists", (
                f"Expected success or 'Did already exists', got: {err}"
            )

    def test_submit_with_valid_dates_is_accepted(self, access_token):
        ok, err = call_submit_to_iir(
            TEST_CTID,
            TEST_DID_KEY,
            "Acme Test",
            "Acme Test Corp",
            "https://registry.example.com",
            "https://acme.example.com",
            access_token,
            PUBLISHER_BASE,
            ssl_verify=False,
            valid_from="2024-01-01T00:00:00Z",
            valid_until="2025-01-01T00:00:00Z",
        )
        if not ok:
            assert err == "Did already exists", (
                f"Expected success or 'Did already exists', got: {err}"
            )

    def test_submit_with_logo_uri_is_accepted(self, access_token):
        # Just making sure the optional logo_uri field round-trips.
        ok, err = call_submit_to_iir(
            TEST_CTID,
            TEST_DID_KEY,
            "Acme Test",
            "Acme Test Corp",
            "https://registry.example.com",
            "https://acme.example.com",
            access_token,
            PUBLISHER_BASE,
            ssl_verify=False,
            logo_uri="https://acme.example.com/logo.png",
        )
        if not ok:
            assert err == "Did already exists", (
                f"Expected success or 'Did already exists', got: {err}"
            )


class TestMergeAutofillEndToEnd:
    def test_registry_data_flows_through_merge(self, access_token):
        ok_reg, registry_data, err_reg = call_get_registry_resource(
            TEST_CTID, access_token, PUBLISHER_BASE, ssl_verify=False
        )
        assert ok_reg, f"Registry lookup failed: {err_reg}"

        ok_acc, accounts_data, _ = call_get_organization_iir_detail(
            TEST_CTID, access_token, PUBLISHER_BASE, ssl_verify=False
        )
        accounts = accounts_data if ok_acc else {}

        merged = merge_autofill(registry_data, accounts)

        expected_keys = {
            "name",
            "legal_name",
            "registry_uri",
            "subject_webpage",
            "image",
            "logo_base64",
        }
        assert set(merged.keys()) == expected_keys, (
            f"merge_autofill output shape changed: {set(merged.keys())}"
        )

        assert merged["name"], (
            f"Expected non-empty name from registry. "
            f"Registry data keys: {list(registry_data.keys())}"
        )

    def test_accounts_legal_name_overrides_when_present(self, access_token):
        ok_reg, registry_data, _ = call_get_registry_resource(
            TEST_CTID, access_token, PUBLISHER_BASE, ssl_verify=False
        )
        assert ok_reg

        ok_acc, accounts_data, _ = call_get_organization_iir_detail(
            TEST_CTID, access_token, PUBLISHER_BASE, ssl_verify=False
        )
        if not ok_acc or not accounts_data.get("LegalName"):
            pytest.skip("Test org has no Accounts LegalName — can't verify override")

        merged = merge_autofill(registry_data, accounts_data)
        assert merged["legal_name"] == accounts_data["LegalName"]


class TestValidateDidDispatcherIntegration:
    def test_did_key_returns_verification_method_for_known_did(self, access_token):
        ok, vm_ids, _data, err = call_validate_did(
            TEST_DID_KEY,
            TEST_ALG,
            access_token,
            PUBLISHER_BASE,
            ssl_verify=False,
        )
        assert ok, f"call_validate_did failed for did:key: {err}"
        assert isinstance(vm_ids, list)
        assert vm_ids, "Expected at least one verification method ID"
        assert any(TEST_DID_KEY in vm for vm in vm_ids), (
            f"Expected '{TEST_DID_KEY}' in verification method IDs: {vm_ids}"
        )

    def test_did_web_returns_verification_method_for_known_did(self, access_token):
        if not TEST_DID_WEB:
            pytest.skip("CE_TEST_DID_WEB not set — skipping did:web dispatcher test.")

        ok, vm_ids, _data, err = call_validate_did(
            TEST_DID_WEB,
            "",  # alg isn't used for did:web
            access_token,
            PUBLISHER_BASE,
            ssl_verify=False,
        )
        assert ok, f"call_validate_did failed for did:web: {err}"
        assert isinstance(vm_ids, list)
        assert vm_ids, "Expected at least one verification method ID"

    def test_unsupported_did_method_short_circuits_without_api_call(self, access_token):
        # Dispatcher should reject unknown methods locally — no point burning
        # an API call on something we know we can't handle.
        ok, vm_ids, _data, err = call_validate_did(
            "did:ethr:0x123",
            "",
            access_token,
            PUBLISHER_BASE,
            ssl_verify=False,
        )
        assert not ok
        assert vm_ids == []
        assert "unrecognised" in err.lower()