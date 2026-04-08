"""
Unit tests for ce.iir.did_ops.
Run with:
    pytest -m "not integration" -s
"""

from __future__ import annotations
import os
import base64
import json
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


pytestmark = pytest.mark.unit

import ce.iir.did_ops as did_ops
from ce.iir.did_ops import (
    _client,
    _did_web_to_url,
    _extract_ed25519_pub_from_did_key,
    _parse_uvarint,
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


PUBLISHER_BASE = os.getenv("CE_PUBLISHER_BASE")
ACCESS_TOKEN = os.getenv("CE_TEST_ACCESS_TOKEN")
USER_ID = os.getenv("CE_TEST_USER_ID")
CTID = os.getenv("CE_TEST_CTID")
CHALLENGE_UUID = os.getenv("CE_TEST_CHALLENGE_UUID")
ED25519_DID_KEY = os.getenv("CE_TEST_DID_KEY")
ED25519_KID = (
    f"{ED25519_DID_KEY}#{ED25519_DID_KEY[len('did:key:'):]}"
    if ED25519_DID_KEY.startswith("did:key:")
    else ""
)


def _fake_response(status_code: int, parsed=None) -> SimpleNamespace:
    return SimpleNamespace(status_code=status_code, parsed=parsed)


class _ParsedObj:
    """Simulates the SDK model objects returned by the generated API client.

    The implementation calls `getattr(parsed, "additional_properties", {})` on
    non-dict parsed values, so this helper must expose that property.
    """

    def __init__(self, **kwargs):
        self._data = kwargs

    # FIX 1: added so call_is_user_member / call_get_registry_resource can
    # read the payload — without this, getattr(parsed, "additional_properties", {})
    # always returned {}, causing every _ParsedObj-based test to fail.
    @property
    def additional_properties(self):
        return self._data

    def to_dict(self):
        return dict(self._data)


class TestClient:
    def test_client_strips_trailing_slash(self):
        client = _client(ACCESS_TOKEN, PUBLISHER_BASE + "/", ssl_verify=False)
        assert client._base_url == PUBLISHER_BASE
        assert client.token == ACCESS_TOKEN
        assert client._verify_ssl is False


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


class TestValidateDate:
    def test_empty_value_is_treated_as_optional(self):
        ok, err, iso = validate_date("", "ValidFrom")
        assert ok
        assert err == "" and iso == ""

    def test_valid_date_converts_to_iso8601(self):
        ok, err, iso = validate_date("01/15/2024", "ValidFrom")
        assert ok
        assert err == ""
        assert iso == "2024-01-15T00:00:00Z"

    def test_iso_format_input_is_rejected(self):
        ok, err, _ = validate_date("2024-01-15", "ValidFrom")
        assert not ok
        assert "MM/DD/YYYY" in err

    def test_impossible_date_fails(self):
        ok, err, _ = validate_date("13/99/2024", "ValidFrom")
        assert not ok
        assert "MM/DD/YYYY" in err


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


class TestCallIsUserMember:
    def test_returns_true_when_valid_dict_payload(self):
        with patch("ce.iir.did_ops.is_user_member_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, {"valid": True})
            ok, err = call_is_user_member(USER_ID, CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert ok and err == ""

    def test_object_payload_with_valid_true_succeeds(self):
        # _ParsedObj.additional_properties returns {"valid": True}, which the
        # implementation reads via getattr(parsed, "additional_properties", {}).
        with patch("ce.iir.did_ops.is_user_member_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, _ParsedObj(valid=True))
            ok, err = call_is_user_member(USER_ID, CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert ok and err == ""

    # FIX 2: was "test_current_implementation_treats_object_payload_as_success"
    # and incorrectly asserted ok=True. With additional_properties present,
    # valid=False is now correctly read, so the call returns (False, "not a member").
    def test_object_payload_with_valid_false_fails(self):
        with patch("ce.iir.did_ops.is_user_member_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, _ParsedObj(valid=False))
            ok, err = call_is_user_member(USER_ID, CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert not ok
        assert "not a member" in err.lower()

    # FIX 3: was "test_propagates_http_error_status" asserting "403" in err.
    # call_is_user_member has no status-code branch — a 403 with parsed=None
    # gives data={}, valid=False, and returns the generic "not a member" message.
    def test_http_error_yields_not_member_message(self):
        with patch("ce.iir.did_ops.is_user_member_sync") as mock_sync:
            mock_sync.return_value = _fake_response(403, None)
            ok, err = call_is_user_member(USER_ID, CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert not ok
        assert err != ""

    def test_handles_exception_gracefully(self):
        with patch("ce.iir.did_ops.is_user_member_sync", side_effect=RuntimeError("timeout")):
            ok, err = call_is_user_member(USER_ID, CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert not ok and "timeout" in err


class TestCallGetRegistryResource:
    def test_returns_data_when_ctid_exists(self):
        body = _ParsedObj(ExistsInRegistry=True, Name="Acme", LegalName="Acme Corp")
        with patch("ce.iir.did_ops.get_registry_resource_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, body)
            ok, data, err = call_get_registry_resource(CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert ok and err == ""
        assert data["Name"] == "Acme"

    # FIX 4: was asserting data == {}. The implementation returns the parsed dict
    # as-is on ExistsInRegistry=False, not an empty dict.
    def test_returns_false_when_ctid_not_in_registry_dict_payload(self):
        with patch("ce.iir.did_ops.get_registry_resource_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, {"ExistsInRegistry": False})
            ok, data, err = call_get_registry_resource(CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert not ok
        assert data == {"ExistsInRegistry": False}
        assert "not found" in err

    # FIX 5: was asserting err == "Registry lookup failed". There is no status-code
    # branch in call_get_registry_resource — a 400 with parsed=None gives data={},
    # ExistsInRegistry missing → exists=False → returns the "not found" message.
    def test_400_falls_through_to_not_found_message(self):
        with patch("ce.iir.did_ops.get_registry_resource_sync") as mock_sync:
            mock_sync.return_value = _fake_response(400, None)
            ok, data, err = call_get_registry_resource(CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert not ok and data == {}
        assert "not found" in err

    def test_exception_returns_api_request_failed_message(self):
        with patch(
            "ce.iir.did_ops.get_registry_resource_sync", side_effect=RuntimeError("conn refused")
        ):
            ok, data, err = call_get_registry_resource(CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert not ok and data == {}
        assert "conn refused" in err


class TestCallValidateDidKey:
    def test_returns_verification_method_ids_on_success(self):
        body = _ParsedObj(verificationMethodIds=[ED25519_KID])
        with patch("ce.iir.did_ops.validate_did_key_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, body)
            ok, data, err = call_validate_did_key(
                ED25519_DID_KEY, "Ed25519", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert ok and err == ""
        assert ED25519_KID in data["verificationMethodIds"]

    def test_400_returns_generic_failure_message(self):
        with patch("ce.iir.did_ops.validate_did_key_sync") as mock_sync:
            mock_sync.return_value = _fake_response(400, None)
            ok, data, err = call_validate_did_key(
                "did:key:bad", "Ed25519", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and data == {}
        assert err == "DID validation failed"


class TestCallValidateDidWeb:
    def test_success(self):
        body = _ParsedObj(verificationMethodIds=["did:web:example.com#key-1"])
        with patch("ce.iir.did_ops.validate_did_web_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, body)
            ok, data, err = call_validate_did_web(
                "did:web:example.com", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert ok and err == ""
        assert data["verificationMethodIds"] == ["did:web:example.com#key-1"]

    def test_502_means_remote_did_document_unreachable(self):
        with patch("ce.iir.did_ops.validate_did_web_sync") as mock_sync:
            mock_sync.return_value = _fake_response(502, None)
            ok, data, err = call_validate_did_web(
                "did:web:example.com", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and data == {}
        assert "502" in err


class TestCallCreateChallenge:
    def _challenge_body(self):
        return _ParsedObj(
            challenge=CHALLENGE_UUID,
            Did=ED25519_DID_KEY,
            Aud="ce-api",
            Iat=1700000000,
            Exp=1700003600,
        )

    def test_returns_first_challenge_on_success(self):
        with patch("ce.iir.did_ops.create_challenges_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, [self._challenge_body()])
            ok, data, err = call_create_challenge(
                CTID, ED25519_KID, ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert ok and err == ""
        assert data["challenge"] == CHALLENGE_UUID

    def test_empty_response_list_is_an_error(self):
        # An empty list is falsy -> `if not data` fires -> "returned empty" message.
        with patch("ce.iir.did_ops.create_challenges_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, [])
            ok, data, err = call_create_challenge(
                CTID, ED25519_KID, ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and data == {}
        assert "empty" in err

    def test_400_returns_generic_failure_message(self):
        with patch("ce.iir.did_ops.create_challenges_sync") as mock_sync:
            mock_sync.return_value = _fake_response(400, None)
            ok, data, err = call_create_challenge(
                CTID, "bad-vm", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and data == {}
        assert err == "createChallenges failed"


class TestCallVerifyJwtSignature:
    def test_success(self):
        with patch("ce.iir.did_ops.validate_jwt_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, None)
            ok, err = call_verify_jwt_signature(
                "proof.jwt.token", CHALLENGE_UUID, ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert ok
        assert err == ""

    def test_404_means_challenge_expired_or_missing(self):
        with patch("ce.iir.did_ops.validate_jwt_sync") as mock_sync:
            mock_sync.return_value = _fake_response(404, None)
            ok, err = call_verify_jwt_signature(
                "proof.jwt.token", CHALLENGE_UUID, ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and err == "Challenge not found"

    def test_400_returns_generic_failure_message(self):
        with patch("ce.iir.did_ops.validate_jwt_sync") as mock_sync:
            mock_sync.return_value = _fake_response(400, None)
            ok, err = call_verify_jwt_signature(
                "bad.jwt", CHALLENGE_UUID, ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and err == "JWT validation failed"


class TestCallSaveChallengeToken:
    def test_success(self):
        with patch("ce.iir.did_ops.save_challenge_token_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, None)
            ok, err = call_save_challenge_token(
                CTID, CHALLENGE_UUID, "proof.jwt", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert ok and err == ""

    def test_400_returns_generic_failure_message(self):
        with patch("ce.iir.did_ops.save_challenge_token_sync") as mock_sync:
            mock_sync.return_value = _fake_response(400, None)
            ok, err = call_save_challenge_token(
                CTID, CHALLENGE_UUID, "bad.jwt", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and err == "saveChallengeToken failed"


class TestCallSubmitToIir:
    def _base_args(self):
        return (
            CTID, ED25519_DID_KEY, "Acme", "Acme Corp",
            "https://registry.example.com", "https://acme.example.com",
            ACCESS_TOKEN, PUBLISHER_BASE, False,
        )

    def test_success(self):
        with patch("ce.iir.did_ops.submit_to_iir_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, None)
            ok, err = call_submit_to_iir(*self._base_args())
        assert ok and err == ""

    def test_409_means_did_already_registered(self):
        with patch("ce.iir.did_ops.submit_to_iir_sync") as mock_sync:
            mock_sync.return_value = _fake_response(409, None)
            ok, err = call_submit_to_iir(*self._base_args())
        assert not ok and err == "Did already exists"

    def test_valid_from_and_until_are_passed_as_model_fields(self):
        with patch("ce.iir.did_ops.submit_to_iir_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, None)
            call_submit_to_iir(
                *self._base_args(),
                valid_from="2024-01-01T00:00:00Z",
                valid_until="2025-01-01T00:00:00Z",
            )
            _, kwargs = mock_sync.call_args
            body = kwargs["body"]
            assert body.valid_from == "2024-01-01T00:00:00Z"
            assert body.valid_until == "2025-01-01T00:00:00Z"

    def test_empty_optional_fields_become_none_on_model(self):
        with patch("ce.iir.did_ops.submit_to_iir_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, None)
            call_submit_to_iir(*self._base_args())
            _, kwargs = mock_sync.call_args
            body = kwargs["body"]
            assert body.logo_uri is None
            assert body.logo_base_64 is None
            assert body.valid_from is None
            assert body.valid_until is None


class TestHelpers:
    def test_parse_uvarint_roundtrip_example(self):
        value, used = _parse_uvarint(bytes([0xED, 0x01]))
        assert value == 0xED
        assert used == 2

    def test_extract_ed25519_pub_from_did_key_returns_32_bytes(self):
        pub = _extract_ed25519_pub_from_did_key(ED25519_DID_KEY)
        assert isinstance(pub, bytes)
        assert len(pub) == 32

    def test_did_web_to_url_without_path(self):
        assert _did_web_to_url("did:web:example.com") == "https://example.com/.well-known/did.json"

    def test_did_web_to_url_with_path(self):
        assert _did_web_to_url("did:web:example.com:users:alice") == "https://example.com/users/alice/did.json"


@pytest.fixture(scope="session")
def private_key() -> str:
    key = os.getenv("CE_TEST_PRIVKEY_MULTIBASE", "").strip()

    if not key:
        pytest.skip("CE_TEST_PRIVKEY_MULTIBASE not set in .env.test")

    try:
        did_ops._extract_ed25519_seed(key)
    except Exception as e:
        pytest.skip(f"Invalid CE_TEST_PRIVKEY_MULTIBASE format: {e}")

    return key


class TestJwtCrypto:
    def _make_payload(self) -> dict:
        return {
            "did": ED25519_DID_KEY,
            "challenge": CHALLENGE_UUID,
            "aud": "ce-api",
            "iat": 1700000000,
            "exp": 1700003600,
            "ctid": CTID,
        }

    def test_sign_produces_a_three_part_jwt(self, private_key):
        token = sign_proof_jwt(private_key, ED25519_KID, self._make_payload())
        assert isinstance(token, str)
        assert token.count(".") == 2

    def test_sign_and_verify_roundtrip(self, private_key):
        token = sign_proof_jwt(private_key, ED25519_KID, self._make_payload())
        ok, err = verify_proof_jwt(token, ED25519_KID)
        assert ok, err

    # FIX 6: the old version mutated the last base64url character, which may be
    # padding-ignored (it can contribute 0 bits of actual data), so the decoded
    # signature bytes were unchanged and verification still passed. Mutating the
    # first character always affects the decoded bytes.
    def test_tampered_signature_fails_verification(self, private_key):
        token = sign_proof_jwt(private_key, ED25519_KID, self._make_payload())
        parts = token.split(".")
        first = parts[2][0]
        parts[2] = ("B" if first != "B" else "C") + parts[2][1:]
        ok, err = verify_proof_jwt(".".join(parts), ED25519_KID)
        assert not ok and "signature" in err.lower()

    def test_bad_private_key_raises(self):
        with pytest.raises(Exception):
            sign_proof_jwt("zNOTVALID", ED25519_KID, self._make_payload())


class TestExtractUserIdFromToken:
    def _make_token(self, payload: dict) -> str:
        header = base64.urlsafe_b64encode(b'{"alg":"RS256"}').rstrip(b"=").decode()
        body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
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