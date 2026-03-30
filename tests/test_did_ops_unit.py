"""
Unit tests 
    pytest -m "not integration" -s
"""

from __future__ import annotations

import base64
import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

import ce.iir.did_ops as did_ops
from ce.iir.did_ops import (
    _url,
    call_create_challenge,
    call_get_registry_resource,
    call_is_user_member,
    call_save_challenge_token,
    call_submit_to_iir,
    call_validate_did_key,
    call_validate_did_web,
    call_verify_jwt_signature,
    classify_did,
    extract_user_id_from_token,
    sign_proof_jwt,
    validate_ctid,
    validate_date,
    validate_did_key_prefix,
    validate_verification_method,
    verify_proof_jwt,
)

# ---------------------------------------------------------------------------
# Constants shared across tests
# ---------------------------------------------------------------------------

PUBLISHER_BASE = "https://localhost:44330"
ACCESS_TOKEN   = "fake.access.token"
USER_ID        = "550e8400-e29b-41d4-a716-446655440000"
CTID           = "ce-12345678-1234-1234-1234-123456789abc"
CHALLENGE_UUID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

ED25519_DID_KEY = "did:key:z6MkgEaGfhgrDL3th8pZG8KZ1DPCX2YLa45GxUNbC2bBLkej"
ED25519_KID     = f"{ED25519_DID_KEY}#{ED25519_DID_KEY[len('did:key:'):]}"


# ---------------------------------------------------------------------------
# Helper — build a fake requests.Response
# ---------------------------------------------------------------------------

def _mock_response(status_code: int, json_body=None, text: str = "") -> MagicMock:
    r = MagicMock()
    r.status_code = status_code
    r.ok = status_code < 400
    r.text = text
    r.json.return_value = json_body or {}
    return r


def _prompt_secret(message: str) -> str:
    """Write a prompt to stderr and read directly from the terminal."""
    sys.stderr.write(message)
    sys.stderr.flush()
    try:
        tty = open("CON" if sys.platform == "win32" else "/dev/tty")
        value = tty.readline().rstrip("\n")
        tty.close()
    except OSError:
        value = ""
    return value.strip()


# ---------------------------------------------------------------------------
# Private key fixture — prompted once per session, never stored
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def private_key() -> str:
    """Return the Ed25519 private key multibase for the test DID.

    Uses CE_TEST_PRIVKEY_MULTIBASE env var if set, otherwise prompts once.
    The key is never written to disk or logged.
    """
    key = os.getenv("CE_TEST_PRIVKEY_MULTIBASE", "").strip()
    if key:
        return key

    sys.stderr.write(
        "\n"
        "  ┌─ Private Key Required (unit tests) ─────────────────────────┐\n"
        "  │  Enter the Ed25519 private key multibase for:               │\n"
        f"  │  {ED25519_DID_KEY[:58]}  │\n"
        "  │  Starts with 'z'. Will not be echoed or stored.             │\n"
        "  └──────────────────────────────────────────────────────────────┘\n"
    )
    key = _prompt_secret("  Private key (z...): ")
    if not key:
        pytest.skip("No private key provided — skipping JWT crypto tests.")
    return key


# ===========================================================================
# Swagger / URL resolution
# ===========================================================================

class TestSwaggerUrlResolution:
    def test_all_known_operations_resolve(self):
        operations = [
            "is_user_member",
            "get_registry_resource",
            "validate_did_web",
            "validate_did_key",
            "create_challenges",
            "validate_jwt",
            "save_challenge_token",
            "submit_to_iir",
        ]
        for op in operations:
            url = _url(op, PUBLISHER_BASE)
            assert url.startswith(PUBLISHER_BASE), f"{op}: URL missing publisher base"
            assert "/api/iir/" in url, f"{op}: URL missing /api/iir/ segment"

    def test_unknown_operation_raises(self):
        with pytest.raises(KeyError, match="Unknown operation"):
            _url("nonexistent_operation", PUBLISHER_BASE)

    def test_trailing_slash_on_base_is_stripped(self):
        url = _url("is_user_member", PUBLISHER_BASE + "/")
        assert "//" not in url.replace("https://", "")

    def test_missing_swagger_file_raises_file_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr(did_ops, "_SWAGGER_FILE", tmp_path / "missing.json")
        did_ops._load_swagger.cache_clear()
        did_ops._path_index.cache_clear()
        with pytest.raises(FileNotFoundError, match="swagger.json"):
            _url("is_user_member", PUBLISHER_BASE)


# ===========================================================================
# validate_ctid
# ===========================================================================

class TestValidateCtid:
    def test_valid_ctid_passes(self):
        ok, err = validate_ctid(CTID)
        assert ok
        assert err == ""

    def test_empty_string_fails(self):
        ok, err = validate_ctid("")
        assert not ok
        assert "empty" in err.lower()

    def test_wrong_format_fails(self):
        ok, err = validate_ctid("not-a-ctid")
        assert not ok
        assert "ce-guid" in err

    def test_ctid_is_case_insensitive(self):
        ok, _ = validate_ctid(CTID.upper())
        assert ok


# ===========================================================================
# validate_date
# ===========================================================================

class TestValidateDate:
    def test_empty_value_is_treated_as_optional(self):
        ok, err, iso = validate_date("", "ValidFrom")
        assert ok
        assert err == "" and iso == ""

    def test_valid_date_converts_to_iso8601(self):
        ok, err, iso = validate_date("01/15/2024", "ValidFrom")
        assert ok
        assert iso == "2024-01-15T00:00:00Z"

    def test_iso_format_input_is_rejected(self):
        ok, err, _ = validate_date("2024-01-15", "ValidFrom")
        assert not ok
        assert "MM/DD/YYYY" in err

    def test_impossible_date_fails(self):
        ok, err, _ = validate_date("13/99/2024", "ValidFrom")
        assert not ok


# ===========================================================================
# classify_did
# ===========================================================================

class TestClassifyDid:
    def test_did_key_recognised(self):
        kind, err = classify_did("did:key:z6Mk...")
        assert kind == "did:key" and err == ""

    def test_did_web_recognised(self):
        kind, err = classify_did("did:web:example.com")
        assert kind == "did:web" and err == ""

    def test_unsupported_method_returns_unknown(self):
        kind, err = classify_did("did:ethr:0x123")
        assert kind == "unknown"
        assert "unrecognised" in err

    def test_empty_did_returns_unknown(self):
        kind, err = classify_did("")
        assert kind == "unknown"
        assert "empty" in err.lower()


# ===========================================================================
# validate_did_key_prefix
# ===========================================================================

class TestValidateDidKeyPrefix:
    def test_ed25519_prefix_matches_algorithm(self):
        ok, _ = validate_did_key_prefix("did:key:z6MkhaXgBZ", "Ed25519")
        assert ok

    def test_prefix_algorithm_mismatch_fails(self):
        ok, err = validate_did_key_prefix("did:key:z6MkhaXgBZ", "P-256")
        assert not ok
        assert "mismatch" in err

    def test_unsupported_algorithm_fails(self):
        ok, err = validate_did_key_prefix("did:key:z6MkhaXgBZ", "RSA")
        assert not ok
        assert "unsupported" in err

    def test_missing_algorithm_fails(self):
        ok, err = validate_did_key_prefix("did:key:z6MkhaXgBZ", "")
        assert not ok
        assert "required" in err

    def test_unrecognised_key_prefix_fails(self):
        ok, err = validate_did_key_prefix("did:key:zXXXunknown", "Ed25519")
        assert not ok
        assert "unrecognised" in err


# ===========================================================================
# validate_verification_method
# ===========================================================================

class TestValidateVerificationMethod:
    def test_valid_vm_in_api_list_passes(self):
        vm = f"{ED25519_DID_KEY}#key-1"
        ok, _ = validate_verification_method(vm, ED25519_DID_KEY, [vm])
        assert ok

    def test_empty_vm_fails(self):
        ok, err = validate_verification_method("", ED25519_DID_KEY, [])
        assert not ok
        assert "empty" in err.lower()

    def test_vm_missing_from_api_list_fails(self):
        ok, err = validate_verification_method(
            f"{ED25519_DID_KEY}#key-1", ED25519_DID_KEY, [f"{ED25519_DID_KEY}#key-2"]
        )
        assert not ok
        assert "not found" in err

    def test_vm_belonging_to_wrong_did_fails(self):
        ok, err = validate_verification_method("did:key:zOTHER#key-1", ED25519_DID_KEY, [])
        assert not ok
        assert "does not belong" in err

    def test_empty_api_list_skips_membership_check(self):
        ok, _ = validate_verification_method(f"{ED25519_DID_KEY}#key-1", ED25519_DID_KEY, [])
        assert ok


# ===========================================================================
# call_is_user_member
# ===========================================================================

class TestCallIsUserMember:
    def test_returns_true_when_valid(self):
        with patch("ce.iir.did_ops.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, {"valid": True})
            ok, err = call_is_user_member(USER_ID, CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert ok and err == ""

    def test_returns_false_when_not_a_member(self):
        with patch("ce.iir.did_ops.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, {"valid": False})
            ok, err = call_is_user_member(USER_ID, CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert not ok
        assert "not a member" in err

    def test_propagates_http_error_status(self):
        with patch("ce.iir.did_ops.requests.get") as mock_get:
            mock_get.return_value = _mock_response(403, text="Forbidden")
            ok, err = call_is_user_member(USER_ID, CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert not ok and "403" in err

    def test_handles_connection_error_gracefully(self):
        import requests as req
        with patch("ce.iir.did_ops.requests.get", side_effect=req.RequestException("timeout")):
            ok, err = call_is_user_member(USER_ID, CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert not ok and "timeout" in err


# ===========================================================================
# call_get_registry_resource
# ===========================================================================

class TestCallGetRegistryResource:
    def test_returns_data_when_ctid_exists(self):
        body = {"ExistsInRegistry": True, "Name": "Acme", "LegalName": "Acme Corp"}
        with patch("ce.iir.did_ops.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, body)
            ok, data, err = call_get_registry_resource(CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert ok and data["Name"] == "Acme"

    def test_returns_false_when_ctid_not_in_registry(self):
        with patch("ce.iir.did_ops.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, {"ExistsInRegistry": False})
            ok, data, err = call_get_registry_resource(CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert not ok and "not found" in err

    def test_surfaces_api_error_message_on_400(self):
        with patch("ce.iir.did_ops.requests.get") as mock_get:
            mock_get.return_value = _mock_response(400, {"message": "bad ctid"})
            ok, data, err = call_get_registry_resource(CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert not ok and "bad ctid" in err


# ===========================================================================
# call_validate_did_key
# ===========================================================================

class TestCallValidateDidKey:
    def test_returns_verification_method_ids_on_success(self):
        body = {"verificationMethodIds": [ED25519_KID]}
        with patch("ce.iir.did_ops.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, body)
            ok, data, err = call_validate_did_key(
                ED25519_DID_KEY, "Ed25519", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert ok and ED25519_KID in data["verificationMethodIds"]

    def test_surfaces_error_message_on_400(self):
        with patch("ce.iir.did_ops.requests.get") as mock_get:
            mock_get.return_value = _mock_response(400, {"message": "invalid did"})
            ok, data, err = call_validate_did_key(
                "did:key:bad", "Ed25519", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and "invalid did" in err


# ===========================================================================
# call_validate_did_web
# ===========================================================================

class TestCallValidateDidWeb:
    def test_success(self):
        body = {"verificationMethodIds": ["did:web:example.com#key-1"]}
        with patch("ce.iir.did_ops.requests.get") as mock_get:
            mock_get.return_value = _mock_response(200, body)
            ok, data, err = call_validate_did_web(
                "did:web:example.com", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert ok

    def test_502_means_remote_did_document_unreachable(self):
        with patch("ce.iir.did_ops.requests.get") as mock_get:
            mock_get.return_value = _mock_response(502)
            ok, data, err = call_validate_did_web(
                "did:web:example.com", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and "502" in err


# ===========================================================================
# call_create_challenge
# ===========================================================================

class TestCallCreateChallenge:
    def _challenge_body(self):
        return {
            "challenge": CHALLENGE_UUID,
            "Did": ED25519_DID_KEY,
            "Aud": "ce-api",
            "Iat": 1700000000,
            "Exp": 1700003600,
        }

    def test_returns_first_challenge_on_success(self):
        with patch("ce.iir.did_ops.requests.post") as mock_post:
            mock_post.return_value = _mock_response(200, [self._challenge_body()])
            ok, data, err = call_create_challenge(
                CTID, ED25519_KID, ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert ok and data["challenge"] == CHALLENGE_UUID

    def test_empty_response_array_is_an_error(self):
        with patch("ce.iir.did_ops.requests.post") as mock_post:
            mock_post.return_value = _mock_response(200, [])
            ok, data, err = call_create_challenge(
                CTID, ED25519_KID, ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and "empty" in err

    def test_surfaces_api_error_on_400(self):
        with patch("ce.iir.did_ops.requests.post") as mock_post:
            mock_post.return_value = _mock_response(400, {"message": "invalid vm"})
            ok, data, err = call_create_challenge(
                CTID, "bad-vm", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and "invalid vm" in err


# ===========================================================================
# call_verify_jwt_signature
# ===========================================================================

class TestCallVerifyJwtSignature:
    def test_success(self):
        with patch("ce.iir.did_ops.requests.post") as mock_post:
            mock_post.return_value = _mock_response(200, {})
            ok, err = call_verify_jwt_signature(
                "proof.jwt.token", CHALLENGE_UUID, ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert ok

    def test_404_means_challenge_expired_or_missing(self):
        with patch("ce.iir.did_ops.requests.post") as mock_post:
            mock_post.return_value = _mock_response(404)
            ok, err = call_verify_jwt_signature(
                "proof.jwt.token", CHALLENGE_UUID, ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and "404" in err

    def test_400_surfaces_validation_error(self):
        with patch("ce.iir.did_ops.requests.post") as mock_post:
            mock_post.return_value = _mock_response(400, {"message": "signature invalid"})
            ok, err = call_verify_jwt_signature(
                "bad.jwt", CHALLENGE_UUID, ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and "signature invalid" in err


# ===========================================================================
# call_save_challenge_token
# ===========================================================================

class TestCallSaveChallengeToken:
    def test_success(self):
        with patch("ce.iir.did_ops.requests.post") as mock_post:
            mock_post.return_value = _mock_response(200, {})
            ok, err = call_save_challenge_token(
                CTID, CHALLENGE_UUID, "proof.jwt", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert ok

    def test_400_surfaces_error_message(self):
        with patch("ce.iir.did_ops.requests.post") as mock_post:
            mock_post.return_value = _mock_response(400, {"message": "bad token"})
            ok, err = call_save_challenge_token(
                CTID, CHALLENGE_UUID, "bad.jwt", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and "bad token" in err


# ===========================================================================
# call_submit_to_iir
# ===========================================================================

class TestCallSubmitToIir:
    def _base_args(self):
        return (
            CTID, ED25519_DID_KEY, "Acme", "Acme Corp",
            "https://registry.example.com", "https://acme.example.com",
            ACCESS_TOKEN, PUBLISHER_BASE, False,
        )

    def test_success(self):
        with patch("ce.iir.did_ops.requests.post") as mock_post:
            mock_post.return_value = _mock_response(200, {})
            ok, err = call_submit_to_iir(*self._base_args())
        assert ok

    def test_409_means_did_already_registered(self):
        with patch("ce.iir.did_ops.requests.post") as mock_post:
            mock_post.return_value = _mock_response(409)
            ok, err = call_submit_to_iir(*self._base_args())
        assert not ok and "409" in err

    def test_valid_from_and_until_included_when_provided(self):
        with patch("ce.iir.did_ops.requests.post") as mock_post:
            mock_post.return_value = _mock_response(200, {})
            call_submit_to_iir(
                *self._base_args(),
                valid_from="2024-01-01T00:00:00Z",
                valid_until="2025-01-01T00:00:00Z",
            )
            _, kwargs = mock_post.call_args
            assert kwargs["json"]["ValidFrom"] == "2024-01-01T00:00:00Z"
            assert kwargs["json"]["ValidUntil"] == "2025-01-01T00:00:00Z"

    def test_valid_from_and_until_omitted_when_empty(self):
        with patch("ce.iir.did_ops.requests.post") as mock_post:
            mock_post.return_value = _mock_response(200, {})
            call_submit_to_iir(*self._base_args())
            _, kwargs = mock_post.call_args
            assert "ValidFrom" not in kwargs["json"]
            assert "ValidUntil" not in kwargs["json"]


# ===========================================================================
# sign_proof_jwt / verify_proof_jwt
# ===========================================================================

class TestJwtCrypto:
    def _make_payload(self) -> dict:
        return {
            "did":       ED25519_DID_KEY,
            "challenge": CHALLENGE_UUID,
            "aud":       "ce-api",
            "iat":       1700000000,
            "exp":       1700003600,
            "ctid":      CTID,
        }

    def test_sign_produces_a_three_part_jwt(self, private_key):
        token = sign_proof_jwt(private_key, ED25519_KID, self._make_payload())
        assert isinstance(token, str)
        assert token.count(".") == 2

    def test_sign_and_verify_roundtrip(self, private_key):
        token = sign_proof_jwt(private_key, ED25519_KID, self._make_payload())
        ok, err = verify_proof_jwt(token, ED25519_KID)
        assert ok, err

    def test_tampered_signature_fails_verification(self, private_key):
        token = sign_proof_jwt(private_key, ED25519_KID, self._make_payload())
        parts = token.split(".")
        parts[2] = parts[2][:-1] + ("A" if parts[2][-1] != "A" else "B")
        ok, err = verify_proof_jwt(".".join(parts), ED25519_KID)
        assert not ok and "signature" in err.lower()

    def test_bad_private_key_raises(self):
        with pytest.raises(Exception):
            sign_proof_jwt("zNOTVALID", ED25519_KID, self._make_payload())


# ===========================================================================
# extract_user_id_from_token
# ===========================================================================

class TestExtractUserIdFromToken:
    def _make_token(self, payload: dict) -> str:
        header = base64.urlsafe_b64encode(b'{"alg":"RS256"}').rstrip(b"=").decode()
        body   = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
        return f"{header}.{body}.fakesig"

    def test_extracts_uuid_sub_claim(self):
        token = self._make_token({"sub": USER_ID})
        assert extract_user_id_from_token(token) == USER_ID

    def test_missing_sub_raises_value_error(self):
        token = self._make_token({"iss": "keycloak"})
        with pytest.raises(ValueError, match="'sub' claim missing"):
            extract_user_id_from_token(token)

    def test_non_uuid_sub_raises_value_error(self):
        token = self._make_token({"sub": "not-a-uuid"})
        with pytest.raises(ValueError, match="not a valid GUID"):
            extract_user_id_from_token(token)

    def test_malformed_token_raises(self):
        with pytest.raises(ValueError):
            extract_user_id_from_token("not.a.jwt.at.all")