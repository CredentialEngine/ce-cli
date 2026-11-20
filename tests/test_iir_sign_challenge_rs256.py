"""
Unit tests for ce.commands.iir_sign_challenge_rs256 (the RS256 path of `ce iir challenge sign`).
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


from ce.commands.iir_sign_challenge_rs256 import (
    _assert_signature_verifiable,
    _did_web_to_url,
    _fetch_did_json,
    _load_private_key_bytes,
    _load_private_key_from_text,
    _load_signing_key,
    _parse_uvarint,
    _public_key_from_did_doc,
    _public_key_from_did_key,
    _resolve_public_key_for_kid,
    _sign_payload,
    _verify_signature_only,
    load_private_key_argument,
    sign_and_verify,
)


MODULE = "ce.commands.iir_sign_challenge_rs256"

CHALLENGE_UUID = "11111111-2222-3333-4444-555555555555"
CTID = "ce-12345678-1234-1234-1234-123456789abc"
ED25519_DID_KEY = "did:key:z6MkhaXgBZDvf7gKKWXjGmgkbQXyrXYY4uZmTaTzPhRgg9Wm"
RSA_MULTICODEC_PREFIX = bytes([0x85, 0x24])  # varint of 0x1205 (rsa-pub)

DID_WEB = "did:web:example.com"
DID_WEB_KID = f"{DID_WEB}#key-1"



# Helpers

def _pem(key, fmt) -> bytes:
    from cryptography.hazmat.primitives import serialization

    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=fmt,
        encryption_algorithm=serialization.NoEncryption(),
    )


def _rsa_did_key(public_key) -> str:
    import base58
    from cryptography.hazmat.primitives import serialization

    pkcs1 = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.PKCS1,
    )
    return "did:key:z" + base58.b58encode(RSA_MULTICODEC_PREFIX + pkcs1).decode()


def _kid_for_did_key(did_key: str) -> str:
    return f"{did_key}#{did_key[len('did:key:'):]}"


def _b64url_uint(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _rsa_jwk(public_key, **extra):
    numbers = public_key.public_numbers()
    jwk = {"kty": "RSA", "n": _b64url_uint(numbers.n), "e": _b64url_uint(numbers.e)}
    jwk.update(extra)
    return jwk


def _did_web_doc(public_key, *, did=DID_WEB, vm_id=DID_WEB_KID, auth=None, vm_type="JsonWebKey2020", jwk=None):
    return {
        "id": did,
        "verificationMethod": [
            {
                "id": vm_id,
                "type": vm_type,
                "controller": did,
                "publicKeyJwk": jwk if jwk is not None else _rsa_jwk(public_key, alg="RS256"),
            }
        ],
        "authentication": [vm_id] if auth is None else auth,
    }


def _decode_segment(token: str, index: int) -> dict:
    segment = token.split(".")[index]
    return json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))


def _tamper_signature(token: str) -> str:
    parts = token.split(".")
    first = parts[2][0]
    parts[2] = ("B" if first != "B" else "C") + parts[2][1:]
    return ".".join(parts)


def _mock_did_json(doc):
    mock_resp = MagicMock()
    mock_resp.json.return_value = doc
    mock_resp.raise_for_status = MagicMock()
    return patch(f"{MODULE}.requests.get", return_value=mock_resp)


def _write_json(path: Path, obj) -> Path:
    path.write_text(json.dumps(obj), encoding="utf-8")
    return path



# Fixtures

@pytest.fixture(scope="session")
def rsa_key():
    from cryptography.hazmat.primitives.asymmetric import rsa

    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="session")
def other_rsa_key():
    from cryptography.hazmat.primitives.asymmetric import rsa

    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="session")
def rsa_kid(rsa_key):
    return _kid_for_did_key(_rsa_did_key(rsa_key.public_key()))


@pytest.fixture
def challenge_payload(rsa_kid):
    return {
        "did": rsa_kid,
        "challenge": CHALLENGE_UUID,
        "aud": "ce-api",
        "iat": 1700000000,
        "exp": 1700003600,
        "ctid": CTID,
    }



class TestParseUvarint:
    def test_rsa_multicodec(self):
        value, used = _parse_uvarint(RSA_MULTICODEC_PREFIX)
        assert value == 0x1205 and used == 2

    def test_invalid_varint_raises(self):
        with pytest.raises(ValueError, match="Invalid varint"):
            _parse_uvarint(bytes([0x80, 0x80, 0x80]))



class TestLoadPrivateKey:
    def test_pkcs8_pem(self, rsa_key):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
        key = _load_private_key_bytes(_pem(rsa_key, serialization.PrivateFormat.PKCS8))
        assert isinstance(key, RSAPrivateKey)

    def test_pkcs1_pem(self, rsa_key):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
        key = _load_private_key_bytes(_pem(rsa_key, serialization.PrivateFormat.TraditionalOpenSSL))
        assert isinstance(key, RSAPrivateKey)

    def test_der(self, rsa_key):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
        der = rsa_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        assert isinstance(_load_private_key_bytes(der), RSAPrivateKey)

    def test_ed25519_key_rejected_with_hint(self):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        pem = _pem(Ed25519PrivateKey.generate(), serialization.PrivateFormat.PKCS8)
        with pytest.raises(ValueError, match="ce iir challenge sign"):
            _load_private_key_bytes(pem)

    def test_encrypted_pem_rejected(self, rsa_key):
        from cryptography.hazmat.primitives import serialization
        pem = rsa_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(b"secret"),
        )
        with pytest.raises(ValueError, match="could not be loaded"):
            _load_private_key_bytes(pem)

    def test_text_with_real_newlines(self, rsa_key):
        from cryptography.hazmat.primitives import serialization
        text = _pem(rsa_key, serialization.PrivateFormat.PKCS8).decode()
        assert _load_private_key_from_text(text).key_size == 2048

    def test_text_with_literal_backslash_n(self, rsa_key):
        from cryptography.hazmat.primitives import serialization
        text = _pem(rsa_key, serialization.PrivateFormat.PKCS8).decode().replace("\n", "\\n")
        assert _load_private_key_from_text(text).key_size == 2048

    def test_text_bare_base64_body(self, rsa_key):
        from cryptography.hazmat.primitives import serialization
        body = "".join(
            line
            for line in _pem(rsa_key, serialization.PrivateFormat.PKCS8).decode().splitlines()
            if "-----" not in line
        )
        assert _load_private_key_from_text(body).key_size == 2048

    def test_text_garbage_rejected(self):
        with pytest.raises(ValueError, match="neither PEM nor base64"):
            _load_private_key_from_text("this is not a key!")


class TestLoadSigningKey:
    def test_file(self, rsa_key, tmp_path):
        from cryptography.hazmat.primitives import serialization
        path = tmp_path / "rsa.pem"
        path.write_bytes(_pem(rsa_key, serialization.PrivateFormat.PKCS8))
        assert _load_signing_key(str(path), None).key_size == 2048

    def test_text(self, rsa_key):
        from cryptography.hazmat.primitives import serialization
        text = _pem(rsa_key, serialization.PrivateFormat.TraditionalOpenSSL).decode()
        assert _load_signing_key(None, text).key_size == 2048

    def test_small_key_rejected(self, tmp_path):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        small = rsa.generate_private_key(public_exponent=65537, key_size=1024)
        path = tmp_path / "small.pem"
        path.write_bytes(_pem(small, serialization.PrivateFormat.PKCS8))
        with pytest.raises(click.ClickException, match="2048"):
            _load_signing_key(str(path), None)

    def test_no_option_rejected(self):
        with pytest.raises(click.ClickException, match="exactly one"):
            _load_signing_key(None, None)

    def test_both_options_rejected(self, rsa_key, tmp_path):
        from cryptography.hazmat.primitives import serialization
        pem = _pem(rsa_key, serialization.PrivateFormat.PKCS8)
        path = tmp_path / "rsa.pem"
        path.write_bytes(pem)
        with pytest.raises(click.ClickException, match="exactly one"):
            _load_signing_key(str(path), pem.decode())



class TestPublicKeyFromDidKey:
    def test_bare_did(self, rsa_key):
        did = _rsa_did_key(rsa_key.public_key())
        assert _public_key_from_did_key(did).public_numbers() == rsa_key.public_key().public_numbers()

    def test_kid_with_fragment(self, rsa_key, rsa_kid):
        assert _public_key_from_did_key(rsa_kid).public_numbers() == rsa_key.public_key().public_numbers()

    def test_did_starts_with_z4mx(self, rsa_key):
        assert _rsa_did_key(rsa_key.public_key()).startswith("did:key:z4MX")

    def test_wrong_fragment_rejected(self, rsa_key):
        did = _rsa_did_key(rsa_key.public_key())
        with pytest.raises(ValueError, match="fragment must equal"):
            _public_key_from_did_key(f"{did}#key-1")

    def test_ed25519_did_key_rejected(self):
        with pytest.raises(ValueError, match="0xED is not an RSA public key"):
            _public_key_from_did_key(ED25519_DID_KEY)

    def test_spki_instead_of_pkcs1_rejected(self, rsa_key):
        import base58
        from cryptography.hazmat.primitives import serialization
        spki = rsa_key.public_key().public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        did = "did:key:z" + base58.b58encode(RSA_MULTICODEC_PREFIX + spki).decode()
        with pytest.raises(ValueError, match="PKCS#1"):
            _public_key_from_did_key(did)

    def test_garbage_key_bytes_rejected(self):
        import base58
        did = "did:key:z" + base58.b58encode(RSA_MULTICODEC_PREFIX + b"\x01" * 32).decode()
        with pytest.raises(ValueError, match="not valid PKCS#1"):
            _public_key_from_did_key(did)

    def test_non_did_key_rejected(self):
        with pytest.raises(ValueError, match="did:key"):
            _public_key_from_did_key(DID_WEB)



class TestDidWebToUrl:
    def test_host_only_uses_well_known(self):
        assert _did_web_to_url(DID_WEB) == "https://example.com/.well-known/did.json"

    def test_with_path_segments(self):
        assert (
            _did_web_to_url("did:web:example.com:issuers:test")
            == "https://example.com/issuers/test/did.json"
        )

    def test_port_is_decoded(self):
        assert (
            _did_web_to_url("did:web:example.com%3A8443")
            == "https://example.com:8443/.well-known/did.json"
        )

    def test_non_did_web_rejected(self):
        with pytest.raises(ValueError, match="did:web"):
            _did_web_to_url("did:key:z4MX...")

    def test_host_with_slash_rejected(self):
        with pytest.raises(ValueError, match="host"):
            _did_web_to_url("did:web:example.com%2Fevil")


class TestFetchDidJson:
    def test_returns_parsed_json(self):
        doc = {"id": DID_WEB, "verificationMethod": []}
        with _mock_did_json(doc) as mock_get:
            assert _fetch_did_json(DID_WEB) == doc

        args, kwargs = mock_get.call_args
        assert args[0] == "https://example.com/.well-known/did.json"
        assert "Accept" in kwargs["headers"]

    def test_http_error_propagates(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        with patch(f"{MODULE}.requests.get", return_value=mock_resp):
            with pytest.raises(requests.HTTPError):
                _fetch_did_json(DID_WEB)

    def test_non_object_rejected(self):
        with _mock_did_json(["not", "an", "object"]):
            with pytest.raises(ValueError, match="must be a JSON object"):
                _fetch_did_json(DID_WEB)


class TestPublicKeyFromDidDoc:
    def test_absolute_ids(self, rsa_key):
        doc = _did_web_doc(rsa_key.public_key())
        key = _public_key_from_did_doc(kid=DID_WEB_KID, did_doc=doc)
        assert key.public_numbers() == rsa_key.public_key().public_numbers()

    def test_relative_ids(self, rsa_key):
        doc = _did_web_doc(rsa_key.public_key(), vm_id="#key-1", auth=["#key-1"])
        key = _public_key_from_did_doc(kid=DID_WEB_KID, did_doc=doc)
        assert key.public_numbers() == rsa_key.public_key().public_numbers()

    def test_embedded_authentication_method(self, rsa_key):
        doc = {
            "id": DID_WEB,
            "authentication": [
                {"id": DID_WEB_KID, "type": "JsonWebKey2020", "publicKeyJwk": _rsa_jwk(rsa_key.public_key())}
            ],
        }
        key = _public_key_from_did_doc(kid=DID_WEB_KID, did_doc=doc)
        assert key.public_numbers() == rsa_key.public_key().public_numbers()

    def test_picks_rsa_key_from_mixed_doc(self, rsa_key):
        doc = _did_web_doc(rsa_key.public_key(), vm_id=f"{DID_WEB}#key-2", auth=[f"{DID_WEB}#key-1", f"{DID_WEB}#key-2"])
        doc["verificationMethod"].insert(
            0,
            {"id": f"{DID_WEB}#key-1", "type": "Ed25519VerificationKey2020", "publicKeyMultibase": "z6Mk..."},
        )
        key = _public_key_from_did_doc(kid=f"{DID_WEB}#key-2", did_doc=doc)
        assert key.public_numbers() == rsa_key.public_key().public_numbers()

    def test_document_id_mismatch_rejected(self, rsa_key):
        doc = _did_web_doc(rsa_key.public_key())
        doc["id"] = "did:web:other.example.com"
        with pytest.raises(ValueError, match="'id' does not match"):
            _public_key_from_did_doc(kid=DID_WEB_KID, did_doc=doc)

    def test_kid_not_found_rejected(self, rsa_key):
        doc = _did_web_doc(rsa_key.public_key())
        with pytest.raises(ValueError, match="kid not found"):
            _public_key_from_did_doc(kid=f"{DID_WEB}#key-MISSING", did_doc=doc)

    def test_not_in_authentication_rejected(self, rsa_key):
        doc = _did_web_doc(rsa_key.public_key(), auth=[])
        with pytest.raises(ValueError, match="not listed under 'authentication'"):
            _public_key_from_did_doc(kid=DID_WEB_KID, did_doc=doc)

    def test_assertion_method_only_rejected(self, rsa_key):
        doc = _did_web_doc(rsa_key.public_key(), auth=[])
        doc["assertionMethod"] = [DID_WEB_KID]
        with pytest.raises(ValueError, match="not listed under 'authentication'"):
            _public_key_from_did_doc(kid=DID_WEB_KID, did_doc=doc)

    def test_wrong_type_rejected(self, rsa_key):
        doc = _did_web_doc(rsa_key.public_key(), vm_type="RsaVerificationKey2018")
        with pytest.raises(ValueError, match="expected 'JsonWebKey2020'"):
            _public_key_from_did_doc(kid=DID_WEB_KID, did_doc=doc)

    def test_non_rsa_jwk_rejected(self, rsa_key):
        doc = _did_web_doc(rsa_key.public_key(), jwk={"kty": "OKP", "crv": "Ed25519", "x": "AAAA"})
        with pytest.raises(ValueError, match="'kty' is 'OKP'"):
            _public_key_from_did_doc(kid=DID_WEB_KID, did_doc=doc)

    def test_private_part_rejected(self, rsa_key):
        doc = _did_web_doc(rsa_key.public_key(), jwk=_rsa_jwk(rsa_key.public_key(), d="AAAA"))
        with pytest.raises(ValueError, match="private key material"):
            _public_key_from_did_doc(kid=DID_WEB_KID, did_doc=doc)

    def test_wrong_jwk_alg_rejected(self, rsa_key):
        doc = _did_web_doc(rsa_key.public_key(), jwk=_rsa_jwk(rsa_key.public_key(), alg="PS256"))
        with pytest.raises(ValueError, match="'alg' is 'PS256'"):
            _public_key_from_did_doc(kid=DID_WEB_KID, did_doc=doc)

    def test_wrong_jwk_use_rejected(self, rsa_key):
        doc = _did_web_doc(rsa_key.public_key(), jwk=_rsa_jwk(rsa_key.public_key(), use="enc"))
        with pytest.raises(ValueError, match="'use' is 'enc'"):
            _public_key_from_did_doc(kid=DID_WEB_KID, did_doc=doc)


class TestResolvePublicKeyForKid:
    def test_did_key(self, rsa_key, rsa_kid):
        assert _resolve_public_key_for_kid(rsa_kid).public_numbers() == rsa_key.public_key().public_numbers()

    def test_did_web_fetches_doc(self, rsa_key):
        with _mock_did_json(_did_web_doc(rsa_key.public_key())) as mock_get:
            key = _resolve_public_key_for_kid(DID_WEB_KID)
        assert key.public_numbers() == rsa_key.public_key().public_numbers()
        assert mock_get.call_args[0][0] == "https://example.com/.well-known/did.json"

    def test_unsupported_method_rejected(self):
        with pytest.raises(ValueError, match="Unsupported DID method"):
            _resolve_public_key_for_kid("did:ethr:0x123#key-1")



class TestSignPayload:
    def test_header(self, rsa_key, rsa_kid, challenge_payload):
        header = _decode_segment(_sign_payload(rsa_key, rsa_kid, challenge_payload), 0)
        assert header == {"typ": "JWT", "alg": "RS256", "kid": rsa_kid}

    def test_payload_round_trips(self, rsa_key, rsa_kid, challenge_payload):
        token = _sign_payload(rsa_key, rsa_kid, challenge_payload)
        assert _decode_segment(token, 1) == challenge_payload

    def test_signature_is_modulus_length(self, rsa_key, rsa_kid, challenge_payload):
        segment = _sign_payload(rsa_key, rsa_kid, challenge_payload).split(".")[2]
        signature = base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))
        assert len(signature) == 256


class TestVerifySignatureOnly:
    def test_valid(self, rsa_key, rsa_kid, challenge_payload):
        token = _sign_payload(rsa_key, rsa_kid, challenge_payload)
        _verify_signature_only(token, rsa_key.public_key())

    def test_tampered_rejected(self, rsa_key, rsa_kid, challenge_payload):
        import jwt
        token = _sign_payload(rsa_key, rsa_kid, challenge_payload)
        with pytest.raises(jwt.exceptions.InvalidSignatureError):
            _verify_signature_only(_tamper_signature(token), rsa_key.public_key())

    def test_does_not_check_expiry(self, rsa_key, rsa_kid):
        payload = {"did": rsa_kid, "challenge": CHALLENGE_UUID, "aud": "ce-api", "iat": 1, "exp": 2}
        token = _sign_payload(rsa_key, rsa_kid, payload)
        _verify_signature_only(token, rsa_key.public_key())


class TestAssertSignatureVerifiable:
    def test_did_key_ok(self, rsa_key, rsa_kid, challenge_payload):
        _assert_signature_verifiable(_sign_payload(rsa_key, rsa_kid, challenge_payload), rsa_kid)

    def test_did_web_ok(self, rsa_key, challenge_payload):
        token = _sign_payload(rsa_key, DID_WEB_KID, challenge_payload)
        with _mock_did_json(_did_web_doc(rsa_key.public_key())):
            _assert_signature_verifiable(token, DID_WEB_KID)

    def test_wrong_key_rejected(self, rsa_key, other_rsa_key, rsa_kid, challenge_payload):
        token = _sign_payload(other_rsa_key, rsa_kid, challenge_payload)
        with pytest.raises(click.ClickException, match="Signature verification failed"):
            _assert_signature_verifiable(token, rsa_kid)

    def test_tampered_rejected(self, rsa_key, rsa_kid, challenge_payload):
        token = _sign_payload(rsa_key, rsa_kid, challenge_payload)
        with pytest.raises(click.ClickException, match="Signature verification failed"):
            _assert_signature_verifiable(_tamper_signature(token), rsa_kid)

    def test_malformed_token_rejected(self, rsa_kid):
        with pytest.raises(click.ClickException, match="JWT verification error"):
            _assert_signature_verifiable("not.a.real.jwt", rsa_kid)



class TestLoadPrivateKeyArgument:
    def test_file_path(self, rsa_key, tmp_path):
        from cryptography.hazmat.primitives import serialization
        path = tmp_path / "rsa.pem"
        path.write_bytes(_pem(rsa_key, serialization.PrivateFormat.PKCS8))
        assert load_private_key_argument(str(path)).key_size == 2048

    def test_pem_text(self, rsa_key):
        from cryptography.hazmat.primitives import serialization
        text = _pem(rsa_key, serialization.PrivateFormat.PKCS8).decode()
        assert load_private_key_argument(text).key_size == 2048

    def test_pem_text_with_literal_backslash_n(self, rsa_key):
        from cryptography.hazmat.primitives import serialization
        text = _pem(rsa_key, serialization.PrivateFormat.PKCS8).decode().replace("\n", "\\n")
        assert load_private_key_argument(text).key_size == 2048

    def test_bare_base64_body(self, rsa_key):
        from cryptography.hazmat.primitives import serialization
        body = "".join(
            line
            for line in _pem(rsa_key, serialization.PrivateFormat.PKCS8).decode().splitlines()
            if "-----" not in line
        )
        assert load_private_key_argument(body).key_size == 2048

    def test_missing_file(self, tmp_path):
        with pytest.raises(click.ClickException, match="RSA private key file not found"):
            load_private_key_argument(str(tmp_path / "missing.pem"))

    def test_ed25519_multibase_gets_hint(self):
        with pytest.raises(click.ClickException, match="--algorithm Ed25519"):
            load_private_key_argument("z3u2en7t5LR2WtQH5PfsRMHEsVGzpW2GZaRcX5qnwX4bBEzhJR")

    def test_ed25519_pem_rejected(self, tmp_path):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        path = tmp_path / "ed.pem"
        path.write_bytes(_pem(Ed25519PrivateKey.generate(), serialization.PrivateFormat.PKCS8))
        with pytest.raises(click.ClickException, match="Expected an RSA private key"):
            load_private_key_argument(str(path))

    def test_small_key_rejected(self, tmp_path):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        path = tmp_path / "small.pem"
        path.write_bytes(_pem(rsa.generate_private_key(public_exponent=65537, key_size=1024), serialization.PrivateFormat.PKCS8))
        with pytest.raises(click.ClickException, match="2048"):
            load_private_key_argument(str(path))

    def test_empty_rejected(self):
        with pytest.raises(click.ClickException, match="empty"):
            load_private_key_argument("   ")


class TestSignAndVerify:
    def test_did_key(self, rsa_key, rsa_kid, tmp_path, challenge_payload):
        from cryptography.hazmat.primitives import serialization
        path = tmp_path / "rsa.pem"
        path.write_bytes(_pem(rsa_key, serialization.PrivateFormat.PKCS8))

        token = sign_and_verify(str(path), rsa_kid, challenge_payload)

        assert _decode_segment(token, 0) == {"typ": "JWT", "alg": "RS256", "kid": rsa_kid}
        assert _decode_segment(token, 1) == challenge_payload

    def test_did_web(self, rsa_key, challenge_payload):
        from cryptography.hazmat.primitives import serialization
        text = _pem(rsa_key, serialization.PrivateFormat.PKCS8).decode()

        with _mock_did_json(_did_web_doc(rsa_key.public_key())):
            token = sign_and_verify(text, DID_WEB_KID, dict(challenge_payload, did=DID_WEB_KID))

        assert _decode_segment(token, 0)["kid"] == DID_WEB_KID

    def test_wrong_key_for_did(self, other_rsa_key, rsa_kid, challenge_payload):
        from cryptography.hazmat.primitives import serialization
        text = _pem(other_rsa_key, serialization.PrivateFormat.PKCS8).decode()
        with pytest.raises(click.ClickException, match="Signature verification failed"):
            sign_and_verify(text, rsa_kid, challenge_payload)

    def test_ed25519_did_rejected(self, rsa_key, challenge_payload):
        from cryptography.hazmat.primitives import serialization
        text = _pem(rsa_key, serialization.PrivateFormat.PKCS8).decode()
        with pytest.raises(click.ClickException, match="not an RSA public key"):
            sign_and_verify(text, ED25519_DID_KEY, dict(challenge_payload, did=ED25519_DID_KEY))

    def test_did_web_fetch_error(self, rsa_key, challenge_payload):
        from cryptography.hazmat.primitives import serialization
        text = _pem(rsa_key, serialization.PrivateFormat.PKCS8).decode()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        with patch(f"{MODULE}.requests.get", return_value=mock_resp):
            with pytest.raises(click.ClickException, match="Failed to fetch did.json"):
                sign_and_verify(text, DID_WEB_KID, dict(challenge_payload, did=DID_WEB_KID))
