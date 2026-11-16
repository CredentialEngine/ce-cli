"""
Unit tests for ce.iir.did_ops.
Run with:
    pytest -m unit -s
"""

from __future__ import annotations
import base64
import json
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest


pytestmark = pytest.mark.unit


from ce.iir.did_ops import (
    IIR_TASK,
    _client,
    _did_web_to_url,
    _extract_ed25519_pub_from_did_key,
    _parse_uvarint,
    _parsed_to_dict,
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
    classify_did,
    extract_user_id_from_token,
    merge_autofill,
    sign_proof_jwt,
    validate_ctid,
    validate_date,
    validate_date_range,
    validate_did_key_prefix,
    validate_verification_method,
    verify_proof_jwt,
)
from ce.iir.api.iir_client.types import UNSET


#Test parameters
PUBLISHER_BASE = "https://fake-publisher.test"
ACCESS_TOKEN = "fake-token-for-unit-tests"
USER_ID = "00000000-0000-0000-0000-000000000001"
CTID = "ce-12345678-1234-1234-1234-123456789abc"
CHALLENGE_UUID = "11111111-2222-3333-4444-555555555555"

ED25519_DID_KEY = "did:key:z6MkhaXgBZDvf7gKKWXjGmgkbQXyrXYY4uZmTaTzPhRgg9Wm"
ED25519_KID = f"{ED25519_DID_KEY}#{ED25519_DID_KEY[len('did:key:'):]}"

def _fake_response(status_code: int, parsed=None) -> SimpleNamespace:
    return SimpleNamespace(status_code=status_code, parsed=parsed)


class _ParsedObj:
    """Simulates the SDK model objects returned by the generated API client.

    The implementation calls `getattr(parsed, "additional_properties", {})` on
    non-dict parsed values, so this helper must expose that property.
    """

    def __init__(self, **kwargs):
        self._data = kwargs

    @property
    def additional_properties(self):
        return self._data

    def to_dict(self):
        return dict(self._data)


@pytest.fixture(scope="session")
def ed25519_keypair():
    """Generate a fresh Ed25519 keypair for crypto tests.

    Returns (private_key_multibase, did_key, kid). The matching public
    key is encoded as a did:key, so signatures created with this private
    key will verify against the returned kid.
    """
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    except ImportError:
        pytest.skip("cryptography package not installed")

    try:
        import base58
    except ImportError:
        pytest.skip("base58 package not installed")

    sk = Ed25519PrivateKey.generate()
    seed = sk.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub = sk.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    # did:key encoding: multicodec prefix 0xed01 (Ed25519 pub) + raw pub bytes,
    # then base58btc encoded with 'z' multibase prefix.
    pub_multicodec = bytes([0xED, 0x01]) + pub
    did_key = "did:key:z" + base58.b58encode(pub_multicodec).decode()

    # Private key in the same multibase form your code expects.
    # Adjust the multicodec prefix if did_ops uses a different encoding.
    priv_multicodec = bytes([0x80, 0x26]) + seed  # 0x8026 = Ed25519 priv multicodec
    priv_multibase = "z" + base58.b58encode(priv_multicodec).decode()

    kid = f"{did_key}#{did_key[len('did:key:'):]}"
    return priv_multibase, did_key, kid


# ---------------------------------------------------------------------------
# Client construction
# ---------------------------------------------------------------------------

class TestClient:
    def test_client_strips_trailing_slash(self):
        client = _client(ACCESS_TOKEN, PUBLISHER_BASE + "/", ssl_verify=False)
        assert client._base_url == PUBLISHER_BASE
        assert client.token == ACCESS_TOKEN
        assert client._verify_ssl is False


class TestParsedToDict:
    """``_parsed_to_dict`` centralises SDK response unwrapping; verify all 3 shapes."""

    def test_dict_passthrough(self):
        assert _parsed_to_dict({"valid": True}) == {"valid": True}

    def test_object_with_to_dict(self):
        assert _parsed_to_dict(_ParsedObj(valid=True, name="x")) == {"valid": True, "name": "x"}

    def test_object_with_only_additional_properties(self):
        class Bare:
            additional_properties = {"valid": False}

        assert _parsed_to_dict(Bare()) == {"valid": False}

    def test_none_returns_empty_dict(self):
        assert _parsed_to_dict(None) == {}

    def test_falsy_returns_empty_dict(self):
        assert _parsed_to_dict({}) == {}


class TestValidateCtid:
    def test_valid_ctid_passes(self):
        ok, err = validate_ctid(CTID)
        assert ok and err == ""

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
        assert ok and err == "" and iso == ""

    def test_valid_date_converts_to_iso8601(self):
        ok, err, iso = validate_date("2024-01-15", "ValidFrom")
        assert ok and err == ""
        assert iso == "2024-01-15T00:00:00Z"

    def test_mm_dd_yyyy_input_is_rejected(self):
        ok, err, _ = validate_date("01/15/2024", "ValidFrom")
        assert not ok
        assert "YYYY-MM-DD" in err

    def test_impossible_date_fails(self):
        ok, err, _ = validate_date("2024-99-99", "ValidFrom")
        assert not ok
        assert "YYYY-MM-DD" in err


class TestValidateDateRange:

    def test_both_empty_is_ok(self):
        ok, err = validate_date_range("", "")
        assert ok and err == ""

    def test_only_from_provided_fails(self):
        ok, err = validate_date_range("2024-01-01", "")
        assert not ok
        assert "both" in err.lower()

    def test_only_until_provided_fails(self):
        ok, err = validate_date_range("", "2024-01-01")
        assert not ok
        assert "both" in err.lower()

    def test_until_before_from_fails(self):
        ok, err = validate_date_range("2024-06-01", "2024-01-01")
        assert not ok
        assert "after" in err.lower()

    def test_until_equal_to_from_fails(self):
        ok, err = validate_date_range("2024-01-01", "2024-01-01")
        assert not ok
        assert "after" in err.lower()

    def test_until_after_from_passes(self):
        ok, err = validate_date_range("2024-01-01", "2024-01-02")
        assert ok and err == ""

    def test_invalid_format_propagates_error(self):
        ok, err = validate_date_range("not-a-date", "2024-01-01")
        assert not ok
        assert "YYYY-MM-DD" in err


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
        with patch("ce.iir.did_ops.is_user_member_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, _ParsedObj(valid=True))
            ok, err = call_is_user_member(USER_ID, CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert ok and err == ""

    def test_object_payload_with_valid_false_fails(self):
        with patch("ce.iir.did_ops.is_user_member_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, _ParsedObj(valid=False))
            ok, err = call_is_user_member(USER_ID, CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert not ok
        assert "not a member" in err.lower()

    def test_http_error_yields_not_member_message(self):
        with patch("ce.iir.did_ops.is_user_member_sync") as mock_sync:
            mock_sync.return_value = _fake_response(403, None)
            ok, err = call_is_user_member(USER_ID, CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert not ok and err != ""

    def test_handles_exception_gracefully(self):
        with patch("ce.iir.did_ops.is_user_member_sync", side_effect=RuntimeError("timeout")):
            ok, err = call_is_user_member(USER_ID, CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert not ok and "timeout" in err

    def test_default_task_is_iir(self):
        with patch("ce.iir.did_ops.is_user_member_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, {"valid": True})
            call_is_user_member(USER_ID, CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
            _, kwargs = mock_sync.call_args
            assert kwargs["task"] == "IIR" == IIR_TASK
            assert kwargs["ctid"] == CTID

    def test_explicit_task_overrides_default(self):
        with patch("ce.iir.did_ops.is_user_member_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, {"valid": True})
            call_is_user_member(
                USER_ID, CTID, ACCESS_TOKEN, PUBLISHER_BASE, False, task="OTHER"
            )
            _, kwargs = mock_sync.call_args
            assert kwargs["task"] == "OTHER"


class TestCallGetRegistryResource:
    def test_returns_data_when_ctid_exists(self):
        body = _ParsedObj(ExistsInRegistry=True, Name="Acme", LegalName="Acme Corp")
        with patch("ce.iir.did_ops.get_registry_resource_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, body)
            ok, data, err = call_get_registry_resource(CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert ok and err == ""
        assert data["Name"] == "Acme"

    def test_returns_false_when_ctid_not_in_registry_dict_payload(self):
        with patch("ce.iir.did_ops.get_registry_resource_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, {"ExistsInRegistry": False})
            ok, data, err = call_get_registry_resource(CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert not ok
        assert data == {"ExistsInRegistry": False}
        assert "not found" in err

    def test_400_falls_through_to_not_found_message(self):
        with patch("ce.iir.did_ops.get_registry_resource_sync") as mock_sync:
            mock_sync.return_value = _fake_response(400, None)
            ok, data, err = call_get_registry_resource(CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert not ok and data == {}
        assert "not found" in err

    def test_exception_returns_api_request_failed_message(self):
        with patch(
            "ce.iir.did_ops.get_registry_resource_sync",
            side_effect=RuntimeError("conn refused"),
        ):
            ok, data, err = call_get_registry_resource(CTID, ACCESS_TOKEN, PUBLISHER_BASE, False)
        assert not ok and data == {}
        assert "conn refused" in err


class TestCallGetOrganizationIIRDetail:
    def test_unwraps_envelope_on_success(self):
        body = _ParsedObj(
            valid=True,
            data={"LegalName": "Acme Corp", "LogoUrl": "https://acme/logo.png"},
        )
        with patch("ce.iir.did_ops.get_organization_iir_detail_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, body)
            ok, data, err = call_get_organization_iir_detail(
                CTID, ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert ok and err == ""
        assert data["LegalName"] == "Acme Corp"
        assert data["LogoUrl"] == "https://acme/logo.png"

    def test_valid_false_returns_failure(self):
        with patch("ce.iir.did_ops.get_organization_iir_detail_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, {"valid": False})
            ok, data, err = call_get_organization_iir_detail(
                CTID, ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok
        assert "not available" in err.lower()

    def test_empty_envelope_returns_failure(self):
        with patch("ce.iir.did_ops.get_organization_iir_detail_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, None)
            ok, data, err = call_get_organization_iir_detail(
                CTID, ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and data == {}
        assert "empty" in err.lower()

    def test_missing_data_key_returns_empty_dict(self):
        with patch("ce.iir.did_ops.get_organization_iir_detail_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, {"valid": True})
            ok, data, err = call_get_organization_iir_detail(
                CTID, ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert ok and err == ""
        assert data == {}

    def test_exception_returns_failure(self):
        with patch(
            "ce.iir.did_ops.get_organization_iir_detail_sync",
            side_effect=RuntimeError("network error"),
        ):
            ok, data, err = call_get_organization_iir_detail(
                CTID, ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and data == {}
        assert "network error" in err


class TestMergeAutofill:
    def test_accounts_legal_name_overrides_registry(self):
        registry = {"Name": "Acme", "LegalName": "Acme Inc.", "Image": "logo.png"}
        accounts = {"LegalName": "Acme Corporation"}
        merged = merge_autofill(registry, accounts)
        assert merged["legal_name"] == "Acme Corporation"
        assert merged["name"] == "Acme"
        assert merged["image"] == "logo.png"

    def test_accounts_logo_only_fills_when_registry_image_empty(self):
        registry = {"Name": "Acme", "LegalName": "", "Image": "registry-logo.png"}
        accounts = {"LegalName": "Acme Corp", "LogoUrl": "accounts-logo.png"}
        merged = merge_autofill(registry, accounts)
        assert merged["image"] == "registry-logo.png"

    def test_accounts_logo_used_when_registry_image_blank(self):
        registry = {"Name": "Acme", "LegalName": "", "Image": ""}
        accounts = {"LegalName": "Acme Corp", "LogoUrl": "accounts-logo.png"}
        merged = merge_autofill(registry, accounts)
        assert merged["image"] == "accounts-logo.png"

    def test_no_accounts_data_falls_back_to_registry(self):
        registry = {
            "Name": "Acme",
            "LegalName": "Acme Inc.",
            "Image": "logo.png",
            "CredentialRegistryUri": "https://registry/x",
            "SubjectWebpage": "https://acme.example",
            "LogoBase64": "abc",
        }
        merged = merge_autofill(registry, {})
        assert merged["legal_name"] == "Acme Inc."
        assert merged["image"] == "logo.png"
        assert merged["registry_uri"] == "https://registry/x"
        assert merged["subject_webpage"] == "https://acme.example"
        assert merged["logo_base64"] == "abc"

    def test_empty_accounts_legal_name_does_not_clear_registry(self):
        registry = {"Name": "Acme", "LegalName": "Acme Inc."}
        accounts = {"LegalName": ""}
        merged = merge_autofill(registry, accounts)
        assert merged["legal_name"] == "Acme Inc."

    def test_handles_missing_registry_keys_gracefully(self):
        merged = merge_autofill({}, {})
        assert merged == {
            "name": "",
            "legal_name": "",
            "registry_uri": "",
            "subject_webpage": "",
            "image": "",
            "logo_base64": "",
        }


class TestCallValidateDidKey:
    def test_returns_verification_method_ids_on_success(self):
        body = _ParsedObj(VerificationMethodIds=[ED25519_KID])
        with patch("ce.iir.did_ops.validate_did_key_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, body)
            ok, data, err = call_validate_did_key(
                ED25519_DID_KEY, "Ed25519", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert ok and err == ""
        assert ED25519_KID in data["VerificationMethodIds"]

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
        body = _ParsedObj(VerificationMethodIds=["did:web:example.com#key-1"])
        with patch("ce.iir.did_ops.validate_did_web_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, body)
            ok, data, err = call_validate_did_web(
                "did:web:example.com", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert ok and err == ""
        assert data["VerificationMethodIds"] == ["did:web:example.com#key-1"]

    def test_502_means_remote_did_document_unreachable(self):
        with patch("ce.iir.did_ops.validate_did_web_sync") as mock_sync:
            mock_sync.return_value = _fake_response(502, None)
            ok, data, err = call_validate_did_web(
                "did:web:example.com", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and data == {}
        assert "502" in err


class TestCallValidateDid:
    def test_did_key_path_returns_vm_ids(self):
        body = _ParsedObj(VerificationMethodIds=[ED25519_KID])
        with patch("ce.iir.did_ops.validate_did_key_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, body)
            ok, vm_ids, data, err = call_validate_did(
                ED25519_DID_KEY, "Ed25519", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert ok and err == ""
        assert vm_ids == [ED25519_KID]
        assert data["VerificationMethodIds"] == [ED25519_KID]

    def test_did_web_path_returns_vm_ids(self):
        body = _ParsedObj(VerificationMethodIds=["did:web:example.com#key-1"])
        with patch("ce.iir.did_ops.validate_did_web_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, body)
            ok, vm_ids, data, err = call_validate_did(
                "did:web:example.com", "", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert ok and err == ""
        assert vm_ids == ["did:web:example.com#key-1"]

    def test_unsupported_did_method_returns_classify_error(self):
        ok, vm_ids, _data, err = call_validate_did(
            "did:ethr:0x123", "", ACCESS_TOKEN, PUBLISHER_BASE, False
        )
        assert not ok
        assert vm_ids == []
        assert "unrecognised" in err

    def test_did_key_with_bad_prefix_short_circuits(self):
        with patch("ce.iir.did_ops.validate_did_key_sync") as mock_sync:
            ok, vm_ids, _, err = call_validate_did(
                "did:key:zXXXunknown", "Ed25519", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and vm_ids == []
        assert "unrecognised" in err.lower()
        mock_sync.assert_not_called()

    def test_missing_vm_ids_returns_empty_list_not_none(self):
        with patch("ce.iir.did_ops.validate_did_web_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, _ParsedObj(somethingElse=True))
            ok, vm_ids, _, err = call_validate_did(
                "did:web:example.com", "", ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert ok and err == ""
        assert vm_ids == []


class TestCallCreateChallenges:
    """Batch challenges: takes a list of vm_ids, returns a list of challenge dicts."""

    def _challenge_body(self, did=None, challenge=None):
        return _ParsedObj(
            Challenge=challenge or CHALLENGE_UUID,
            Did=did or ED25519_DID_KEY,
            Aud="ce-api",
            Iat=1700000000,
            Exp=1700003600,
        )

    def test_returns_list_on_success(self):
        with patch("ce.iir.did_ops.create_challenges_sync") as mock_sync:
            mock_sync.return_value = _fake_response(
                200,
                [
                    self._challenge_body(did=f"{ED25519_DID_KEY}#k1"),
                    self._challenge_body(did=f"{ED25519_DID_KEY}#k2"),
                ],
            )
            ok, data, err = call_create_challenges(
                CTID,
                [f"{ED25519_DID_KEY}#k1", f"{ED25519_DID_KEY}#k2"],
                ACCESS_TOKEN, PUBLISHER_BASE, False,
            )
        assert ok and err == ""
        assert isinstance(data, list)
        assert len(data) == 2
        assert all(c["Challenge"] == CHALLENGE_UUID for c in data)

    def test_passes_all_vm_ids_in_single_request(self):
        vm_ids = [f"{ED25519_DID_KEY}#k1", f"{ED25519_DID_KEY}#k2"]
        with patch("ce.iir.did_ops.create_challenges_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, [self._challenge_body()])
            call_create_challenges(CTID, vm_ids, ACCESS_TOKEN, PUBLISHER_BASE, False)
            _, kwargs = mock_sync.call_args
            body = kwargs["body"]
            assert mock_sync.call_count == 1
            assert body.verification_method_ids == vm_ids
            assert body.ctid == CTID

    def test_empty_vm_ids_short_circuits_without_api_call(self):
        with patch("ce.iir.did_ops.create_challenges_sync") as mock_sync:
            ok, data, err = call_create_challenges(
                CTID, [], ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and data == []
        assert "no verification methods" in err.lower()
        mock_sync.assert_not_called()

    def test_empty_response_list_is_an_error(self):
        with patch("ce.iir.did_ops.create_challenges_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, [])
            ok, data, err = call_create_challenges(
                CTID, [ED25519_KID], ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and data == []
        assert "empty" in err

    def test_400_returns_generic_failure_message(self):
        with patch("ce.iir.did_ops.create_challenges_sync") as mock_sync:
            mock_sync.return_value = _fake_response(400, None)
            ok, data, err = call_create_challenges(
                CTID, ["bad-vm"], ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert not ok and data == []
        assert err == "createChallenges failed"


class TestCallVerifyJwtSignature:
    def test_success(self):
        with patch("ce.iir.did_ops.validate_jwt_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, None)
            ok, err = call_verify_jwt_signature(
                "proof.jwt.token", CHALLENGE_UUID, ACCESS_TOKEN, PUBLISHER_BASE, False
            )
        assert ok and err == ""

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

    @staticmethod
    def _local_date_of_z(z: str) -> date:
        """Parse a 'YYYY-MM-DDT00:00:00Z' string and return its date in local time."""
        dt = datetime.strptime(z, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return dt.astimezone().date()

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

    def test_iso_strings_become_z_strings_in_additional_properties(self):
        with patch("ce.iir.did_ops.submit_to_iir_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, None)
            call_submit_to_iir(
                *self._base_args(),
                valid_from="2024-01-01T00:00:00Z",
                valid_until="2025-01-01T00:00:00Z",
            )
            _, kwargs = mock_sync.call_args
            body = kwargs["body"]
            df = body.additional_properties["DateValidFrom"]
            du = body.additional_properties["DateValidUntil"]
            assert df.endswith("Z") and du.endswith("Z")
            assert self._local_date_of_z(df) == date(2024, 1, 1)
            assert self._local_date_of_z(du) == date(2025, 1, 1)

    def test_yyyy_mm_dd_dates_also_parse(self):
        with patch("ce.iir.did_ops.submit_to_iir_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, None)
            call_submit_to_iir(
                *self._base_args(), valid_from="2024-06-15", valid_until="2025-06-15"
            )
            _, kwargs = mock_sync.call_args
            body = kwargs["body"]
            df = body.additional_properties["DateValidFrom"]
            assert self._local_date_of_z(df) == date(2024, 6, 15)

    def test_dto_to_dict_serializes_dates_under_capitalized_keys(self):
        with patch("ce.iir.did_ops.submit_to_iir_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, None)
            call_submit_to_iir(
                *self._base_args(), valid_from="2024-06-15", valid_until="2025-06-15"
            )
            _, kwargs = mock_sync.call_args
            d = kwargs["body"].to_dict()
            assert d["DateValidFrom"].endswith("Z")
            assert d["DateValidUntil"].endswith("Z")

    def test_empty_optional_fields_are_absent(self):
        with patch("ce.iir.did_ops.submit_to_iir_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, None)
            call_submit_to_iir(*self._base_args())
            _, kwargs = mock_sync.call_args
            body = kwargs["body"]
            assert body.logo_uri is UNSET
            assert body.logo_base_64 is UNSET
            assert body.valid_from is UNSET
            assert body.valid_until is UNSET
            assert "DateValidFrom" not in body.additional_properties
            assert "DateValidUntil" not in body.additional_properties

    def test_dto_to_dict_does_not_crash_on_empty_optionals(self):
        with patch("ce.iir.did_ops.submit_to_iir_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, None)
            call_submit_to_iir(*self._base_args())
            _, kwargs = mock_sync.call_args
            d = kwargs["body"].to_dict()
            assert "ValidFrom" not in d
            assert "ValidUntil" not in d
            assert "DateValidFrom" not in d
            assert "DateValidUntil" not in d
            assert "LogoUri" not in d
            assert "LogoBase64" not in d

    def test_invalid_date_string_is_omitted(self):
        with patch("ce.iir.did_ops.submit_to_iir_sync") as mock_sync:
            mock_sync.return_value = _fake_response(200, None)
            call_submit_to_iir(
                *self._base_args(), valid_from="garbage-date", valid_until=""
            )
            _, kwargs = mock_sync.call_args
            body = kwargs["body"]
            assert "DateValidFrom" not in body.additional_properties
            assert "DateValidUntil" not in body.additional_properties

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
        assert (
            _did_web_to_url("did:web:example.com:users:alice")
            == "https://example.com/users/alice/did.json"
        )



class TestJwtCrypto:
    def _make_payload(self, did_key: str) -> dict:
        return {
            "did": did_key,
            "challenge": CHALLENGE_UUID,
            "aud": "ce-api",
            "iat": 1700000000,
            "exp": 1700003600,
            "ctid": CTID,
        }

    def test_sign_produces_a_three_part_jwt(self, ed25519_keypair):
        priv, did_key, kid = ed25519_keypair
        token = sign_proof_jwt(priv, kid, self._make_payload(did_key))
        assert isinstance(token, str)
        assert token.count(".") == 2

    def test_sign_and_verify_roundtrip(self, ed25519_keypair):
        priv, did_key, kid = ed25519_keypair
        token = sign_proof_jwt(priv, kid, self._make_payload(did_key))
        ok, err = verify_proof_jwt(token, kid)
        assert ok, err

    def test_tampered_signature_fails_verification(self, ed25519_keypair):
        priv, did_key, kid = ed25519_keypair
        token = sign_proof_jwt(priv, kid, self._make_payload(did_key))
        parts = token.split(".")
        first = parts[2][0]
        parts[2] = ("B" if first != "B" else "C") + parts[2][1:]
        ok, err = verify_proof_jwt(".".join(parts), kid)
        assert not ok and "signature" in err.lower()

    def test_bad_private_key_raises(self, ed25519_keypair):
        _, _, kid = ed25519_keypair
        with pytest.raises(Exception):
            sign_proof_jwt("zNOTVALID", kid, self._make_payload(ED25519_DID_KEY))


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