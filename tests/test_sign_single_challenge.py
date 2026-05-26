"""
Unit tests for ce.commands.iir_sign_challenge.
Run with:
    pytest -m unit -s
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import pytest
import requests



pytestmark = pytest.mark.unit


from ce.commands.iir_sign_challenge import (
    _assert_signature_verifiable,
    _decode_multibase_base58btc,
    _did_web_to_url,
    _extract_ed25519_pub_from_did_key,
    _extract_ed25519_seed_from_private_key,
    _fetch_did_json,
    _parse_uvarint,
    _public_key_from_did_doc,
    _resolve_public_key_bytes_for_kid,
    _sign_payload,
    _verify_signature_only,
)



CHALLENGE_UUID = "11111111-2222-3333-4444-555555555555"
CTID = "ce-12345678-1234-1234-1234-123456789abc"
ED25519_DID_KEY = "did:key:z6MkhaXgBZDvf7gKKWXjGmgkbQXyrXYY4uZmTaTzPhRgg9Wm"
ED25519_KID = f"{ED25519_DID_KEY}#{ED25519_DID_KEY[len('did:key:'):]}"


@pytest.fixture(scope="session")
def ed25519_keypair():
    """Generate a fresh Ed25519 keypair as (priv_multibase, did_key, kid).

    The public key is encoded as a did:key and the private key uses the
    same 32-byte raw multibase encoding the module's seed extractor
    accepts, so signing+verification roundtrips work end-to-end.
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

    did_key = "did:key:z" + base58.b58encode(bytes([0xED, 0x01]) + pub).decode()
    kid = f"{did_key}#{did_key[len('did:key:'):]}"

    priv_multibase = "z" + base58.b58encode(seed).decode()

    return priv_multibase, did_key, kid


@pytest.fixture
def valid_challenge_payload():
    return {
        "did": ED25519_DID_KEY,
        "challenge": CHALLENGE_UUID,
        "aud": "ce-api",
        "iat": 1700000000,
        "exp": 1700003600,
        "ctid": CTID,
    }


def _write_json(path: Path, obj) -> Path:
    path.write_text(json.dumps(obj), encoding="utf-8")
    return path



class TestParseUvarint:
    def test_single_byte_value(self):
        value, used = _parse_uvarint(bytes([0x7F]))
        assert value == 0x7F and used == 1

    def test_two_byte_continuation(self):
        value, used = _parse_uvarint(bytes([0x80, 0x01]))
        assert value == 128 and used == 2

    def test_consumes_only_the_varint_bytes(self):
        value, used = _parse_uvarint(bytes([0x7F, 0xAA, 0xBB]))
        assert value == 0x7F and used == 1

    def test_invalid_varint_raises(self):
        with pytest.raises(ValueError, match="Invalid varint"):
            _parse_uvarint(bytes([0x80, 0x80, 0x80]))


class TestDecodeMultibaseBase58btc:
    def test_round_trip(self):
        import base58
        raw = b"hello world"
        encoded = "z" + base58.b58encode(raw).decode()
        assert _decode_multibase_base58btc(encoded) == raw

    def test_missing_z_prefix_raises(self):
        with pytest.raises(ValueError, match="multibase"):
            _decode_multibase_base58btc("Mxyz")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            _decode_multibase_base58btc("")



class TestExtractEd25519Seed:
    def test_raw_32_byte_seed(self, ed25519_keypair):
        priv, _, _ = ed25519_keypair
        seed = _extract_ed25519_seed_from_private_key(priv)
        assert isinstance(seed, bytes) and len(seed) == 32

    def test_strips_leading_whitespace(self, ed25519_keypair):
        priv, _, _ = ed25519_keypair
        seed = _extract_ed25519_seed_from_private_key("  " + priv + "\n")
        assert len(seed) == 32

    def test_33_byte_with_leading_zero(self):
        import base58
        raw = bytes([0x00]) + (b"\x01" * 32)
        priv_mb = "z" + base58.b58encode(raw).decode()
        seed = _extract_ed25519_seed_from_private_key(priv_mb)
        assert seed == b"\x01" * 32

    def test_34_byte_with_leading_00_20(self):
        import base58
        raw = bytes([0x00, 0x20]) + (b"\x02" * 32)
        priv_mb = "z" + base58.b58encode(raw).decode()
        seed = _extract_ed25519_seed_from_private_key(priv_mb)
        assert seed == b"\x02" * 32

    def test_multicodec_0x1300_prefix(self):
        import base58
        raw = bytes([0x80, 0x26]) + (b"\x03" * 32)
        priv_mb = "z" + base58.b58encode(raw).decode()
        seed = _extract_ed25519_seed_from_private_key(priv_mb)
        assert seed == b"\x03" * 32

    def test_unknown_encoding_raises(self):
        import base58
        raw = bytes([0x01]) + (b"\x99" * 16)
        priv_mb = "z" + base58.b58encode(raw).decode()
        with pytest.raises(ValueError, match="Unrecognized privateKey"):
            _extract_ed25519_seed_from_private_key(priv_mb)

    def test_non_multibase_input_raises(self):
        with pytest.raises(ValueError):
            _extract_ed25519_seed_from_private_key("not-multibase")



class TestExtractEd25519PubFromDidKey:
    def test_returns_32_bytes(self):
        pub = _extract_ed25519_pub_from_did_key(ED25519_DID_KEY)
        assert isinstance(pub, bytes) and len(pub) == 32

    def test_accepts_kid_with_fragment(self):
        from_base = _extract_ed25519_pub_from_did_key(ED25519_DID_KEY)
        from_kid = _extract_ed25519_pub_from_did_key(ED25519_KID)
        assert from_base == from_kid

    def test_strips_whitespace(self):
        pub = _extract_ed25519_pub_from_did_key("  " + ED25519_DID_KEY + "  ")
        assert len(pub) == 32

    def test_non_did_key_raises(self):
        with pytest.raises(ValueError, match="did:key"):
            _extract_ed25519_pub_from_did_key("did:web:example.com")

    def test_invalid_multicodec_raises(self):
        import base58
        raw = bytes([0x80, 0x24]) + (b"\x00" * 32)
        bad_did = "did:key:z" + base58.b58encode(raw).decode()
        with pytest.raises(ValueError, match="Invalid did:key"):
            _extract_ed25519_pub_from_did_key(bad_did)


class TestDidWebToUrl:
    def test_host_only_uses_well_known(self):
        assert (
            _did_web_to_url("did:web:example.com")
            == "https://example.com/.well-known/did.json"
        )

    def test_with_path_segments(self):
        assert (
            _did_web_to_url("did:web:example.com:users:alice")
            == "https://example.com/users/alice/did.json"
        )

    def test_host_with_port(self):
        url = _did_web_to_url("did:web:example.com%3A8443")
        assert url.startswith("https://example.com%3A8443/")
        assert url.endswith("/.well-known/did.json")

    def test_non_did_web_raises(self):
        with pytest.raises(ValueError, match="did:web"):
            _did_web_to_url("did:key:z6Mk...")


class TestFetchDidJson:
    def test_returns_parsed_json_on_200(self):
        doc = {"id": "did:web:example.com", "verificationMethod": []}
        mock_resp = MagicMock()
        mock_resp.json.return_value = doc
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "ce.commands.iir_sign_challenge.requests.get",
            return_value=mock_resp,
        ) as mock_get:
            result = _fetch_did_json("did:web:example.com")

        assert result == doc
        args, kwargs = mock_get.call_args
        assert args[0] == "https://example.com/.well-known/did.json"
        assert "Accept" in kwargs["headers"]

    def test_http_error_propagates(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

        with patch(
            "ce.commands.iir_sign_challenge.requests.get",
            return_value=mock_resp,
        ):
            with pytest.raises(requests.HTTPError):
                _fetch_did_json("did:web:example.com")

    def test_non_object_response_raises(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = ["not", "an", "object"]
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "ce.commands.iir_sign_challenge.requests.get",
            return_value=mock_resp,
        ):
            with pytest.raises(ValueError, match="must be a JSON object"):
                _fetch_did_json("did:web:example.com")

    def test_passes_through_path_segments_in_url(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"verificationMethod": []}
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "ce.commands.iir_sign_challenge.requests.get",
            return_value=mock_resp,
        ) as mock_get:
            _fetch_did_json("did:web:example.com:users:alice")

        args, _ = mock_get.call_args
        assert args[0] == "https://example.com/users/alice/did.json"


class TestPublicKeyFromDidDoc:
    def _doc(self, did, vm_id, pub_multibase):
        return {
            "id": did,
            "verificationMethod": [
                {
                    "id": vm_id,
                    "type": "Ed25519VerificationKey2020",
                    "controller": did,
                    "publicKeyMultibase": pub_multibase,
                }
            ],
        }

    def _did_web_keypair(self):
        """Generate a real Ed25519 public key for did:web tests."""
        import base58
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        sk = Ed25519PrivateKey.generate()
        pub = sk.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        pub_mb = "z" + base58.b58encode(bytes([0xED, 0x01]) + pub).decode()
        return pub, pub_mb

    def test_finds_key_by_absolute_kid(self):
        pub, pub_mb = self._did_web_keypair()
        did = "did:web:example.com"
        kid = f"{did}#key-1"
        doc = self._doc(did, kid, pub_mb)

        result = _public_key_from_did_doc(kid=kid, did_doc=doc)
        assert result == pub

    def test_finds_key_when_vm_id_is_relative(self):
        pub, pub_mb = self._did_web_keypair()
        did = "did:web:example.com"
        kid = f"{did}#key-1"
        doc = self._doc(did, "#key-1", pub_mb)

        result = _public_key_from_did_doc(kid=kid, did_doc=doc)
        assert result == pub

    def test_raw_32_byte_pub_multibase_accepted(self):
        import base58
        pub = b"\x05" * 32
        pub_mb = "z" + base58.b58encode(pub).decode()
        did = "did:web:example.com"
        kid = f"{did}#key-1"
        doc = self._doc(did, kid, pub_mb)

        result = _public_key_from_did_doc(kid=kid, did_doc=doc)
        assert result == pub

    def test_kid_not_in_doc_raises(self):
        _, pub_mb = self._did_web_keypair()
        did = "did:web:example.com"
        doc = self._doc(did, f"{did}#key-1", pub_mb)

        with pytest.raises(ValueError, match="kid not found"):
            _public_key_from_did_doc(kid=f"{did}#key-MISSING", did_doc=doc)

    def test_verification_method_must_be_list(self):
        doc = {"id": "did:web:example.com", "verificationMethod": "not-a-list"}
        with pytest.raises(ValueError, match="must be a list"):
            _public_key_from_did_doc(kid="did:web:example.com#key-1", did_doc=doc)

    def test_skips_non_dict_entries(self):
        pub, pub_mb = self._did_web_keypair()
        did = "did:web:example.com"
        kid = f"{did}#key-1"
        doc = {
            "id": did,
            "verificationMethod": [
                "garbage",
                None,
                {"id": kid, "publicKeyMultibase": pub_mb},
            ],
        }
        assert _public_key_from_did_doc(kid=kid, did_doc=doc) == pub

    def test_skips_entries_without_id(self):
        pub, pub_mb = self._did_web_keypair()
        did = "did:web:example.com"
        kid = f"{did}#key-1"
        doc = {
            "id": did,
            "verificationMethod": [
                {"publicKeyMultibase": "zSomething"},  
                {"id": kid, "publicKeyMultibase": pub_mb},
            ],
        }
        assert _public_key_from_did_doc(kid=kid, did_doc=doc) == pub

    def test_invalid_public_key_multibase_raises(self):
        did = "did:web:example.com"
        kid = f"{did}#key-1"
        doc = self._doc(did, kid, "NOT-Z-PREFIXED")

        with pytest.raises(ValueError, match="Invalid publicKeyMultibase"):
            _public_key_from_did_doc(kid=kid, did_doc=doc)

    def test_missing_public_key_multibase_raises(self):
        did = "did:web:example.com"
        kid = f"{did}#key-1"
        doc = {"id": did, "verificationMethod": [{"id": kid}]}

        with pytest.raises(ValueError, match="Invalid publicKeyMultibase"):
            _public_key_from_did_doc(kid=kid, did_doc=doc)

    def test_unrecognized_pub_key_encoding_raises(self):
        import base58
        raw = bytes([0x01]) + (b"\x99" * 16)
        bad_mb = "z" + base58.b58encode(raw).decode()
        did = "did:web:example.com"
        kid = f"{did}#key-1"
        doc = self._doc(did, kid, bad_mb)

        with pytest.raises(ValueError, match="Ed25519"):
            _public_key_from_did_doc(kid=kid, did_doc=doc)


class TestResolvePublicKeyBytesForKid:
    def test_did_key_path(self):
        pub = _resolve_public_key_bytes_for_kid(ED25519_KID)
        assert len(pub) == 32

    def test_did_web_path_fetches_doc(self):
        import base58
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        sk = Ed25519PrivateKey.generate()
        pub = sk.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        pub_mb = "z" + base58.b58encode(bytes([0xED, 0x01]) + pub).decode()

        did = "did:web:example.com"
        kid = f"{did}#key-1"
        doc = {
            "id": did,
            "verificationMethod": [{"id": kid, "publicKeyMultibase": pub_mb}],
        }

        mock_resp = MagicMock()
        mock_resp.json.return_value = doc
        mock_resp.raise_for_status = MagicMock()
        with patch(
            "ce.commands.iir_sign_challenge.requests.get",
            return_value=mock_resp,
        ):
            result = _resolve_public_key_bytes_for_kid(kid)
        assert result == pub

    def test_unsupported_did_method_raises(self):
        with pytest.raises(ValueError, match="Unsupported DID method"):
            _resolve_public_key_bytes_for_kid("did:ethr:0x123#key-1")



class TestSignPayload:
    def test_returns_three_part_jwt_string(self, ed25519_keypair, valid_challenge_payload):
        priv, _, kid = ed25519_keypair
        token = _sign_payload(priv, kid, valid_challenge_payload)
        assert isinstance(token, str)
        assert token.count(".") == 2

    def test_header_includes_alg_typ_kid(self, ed25519_keypair, valid_challenge_payload):
        priv, _, kid = ed25519_keypair
        token = _sign_payload(priv, kid, valid_challenge_payload)
        header_b64 = token.split(".")[0]
        padded = header_b64 + "=" * (-len(header_b64) % 4)
        header = json.loads(base64.urlsafe_b64decode(padded))
        assert header["alg"] == "EdDSA"
        assert header["typ"] == "JWT"
        assert header["kid"] == kid

    def test_payload_round_trips(self, ed25519_keypair, valid_challenge_payload):
        priv, _, kid = ed25519_keypair
        token = _sign_payload(priv, kid, valid_challenge_payload)
        payload_b64 = token.split(".")[1]
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(padded))
        assert decoded == valid_challenge_payload

    def test_bad_private_key_raises(self, valid_challenge_payload):
        with pytest.raises(ValueError):
            _sign_payload("zNOT-A-REAL-KEY", ED25519_KID, valid_challenge_payload)


class TestVerifySignatureOnly:
    def test_valid_signature_returns_none(self, ed25519_keypair, valid_challenge_payload):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        priv, _, kid = ed25519_keypair
        token = _sign_payload(priv, kid, valid_challenge_payload)
        pub_bytes = _extract_ed25519_pub_from_did_key(kid)
        pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)

        _verify_signature_only(token, pub_key)

    def test_tampered_signature_raises(self, ed25519_keypair, valid_challenge_payload):
        import jwt
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        priv, _, kid = ed25519_keypair
        token = _sign_payload(priv, kid, valid_challenge_payload)
        parts = token.split(".")
        first = parts[2][0]
        parts[2] = ("B" if first != "B" else "C") + parts[2][1:]
        tampered = ".".join(parts)

        pub_bytes = _extract_ed25519_pub_from_did_key(kid)
        pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)

        with pytest.raises(jwt.exceptions.InvalidSignatureError):
            _verify_signature_only(tampered, pub_key)

    def test_does_not_check_expiry(self, ed25519_keypair):
        """Even with iat/exp in the past, verification must pass — the
        function exists specifically to verify the signature only."""
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        priv, _, kid = ed25519_keypair
        payload = {
            "did": ED25519_DID_KEY,
            "challenge": CHALLENGE_UUID,
            "aud": "ce-api",
            "iat": 1,
            "exp": 2,
        }
        token = _sign_payload(priv, kid, payload)
        pub_bytes = _extract_ed25519_pub_from_did_key(kid)
        pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)

        _verify_signature_only(token, pub_key)


class TestAssertSignatureVerifiable:
    def test_passes_for_valid_token(self, ed25519_keypair, valid_challenge_payload):
        priv, _, kid = ed25519_keypair
        token = _sign_payload(priv, kid, valid_challenge_payload)
        _assert_signature_verifiable(token, kid)

    def test_tampered_token_raises_click_exception(
        self, ed25519_keypair, valid_challenge_payload
    ):
        priv, _, kid = ed25519_keypair
        token = _sign_payload(priv, kid, valid_challenge_payload)
        parts = token.split(".")
        first = parts[2][0]
        parts[2] = ("B" if first != "B" else "C") + parts[2][1:]
        tampered = ".".join(parts)

        with pytest.raises(click.ClickException, match="Signature verification failed"):
            _assert_signature_verifiable(tampered, kid)

    def test_malformed_token_raises_click_exception(self, ed25519_keypair):
        _, _, kid = ed25519_keypair
        with pytest.raises(click.ClickException, match="JWT verification error"):
            _assert_signature_verifiable("not.a.real.jwt", kid)

