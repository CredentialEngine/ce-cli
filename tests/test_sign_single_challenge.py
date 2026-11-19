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
from click.testing import CliRunner



pytestmark = pytest.mark.unit


from ce.commands.iir_sign_challenge import (
    _assert_signature_verifiable,
    _decode_multibase_base58btc,
    _did_web_to_url,
    _extract_ed25519_seed_from_private_key,
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
    sign_individual_challenge,
)


MODULE = "ce.commands.iir_sign_challenge"

CHALLENGE_UUID = "11111111-2222-3333-4444-555555555555"
CTID = "ce-12345678-1234-1234-1234-123456789abc"
ED25519_DID_KEY = "did:key:z6MkhaXgBZDvf7gKKWXjGmgkbQXyrXYY4uZmTaTzPhRgg9Wm"
ED25519_KID = f"{ED25519_DID_KEY}#{ED25519_DID_KEY[len('did:key:'):]}"

RSA_MULTICODEC_PREFIX = bytes([0x85, 0x24])  # varint of 0x1205



# Helpers

def _raw_ed25519(public_key) -> bytes:
    from cryptography.hazmat.primitives import serialization

    return public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def _b64url_uint(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _rsa_jwk(public_key, **extra):
    numbers = public_key.public_numbers()
    jwk = {"kty": "RSA", "n": _b64url_uint(numbers.n), "e": _b64url_uint(numbers.e)}
    jwk.update(extra)
    return jwk


def _decode_segment(token: str, index: int) -> dict:
    segment = token.split(".")[index]
    padded = segment + "=" * (-len(segment) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


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


@pytest.fixture(scope="session")
def ed25519_signing_key(ed25519_keypair):
    """The Ed25519 private key object for the session keypair."""
    priv, _, _ = ed25519_keypair
    key, alg = _load_signing_key(priv, None, None)
    assert alg == "EdDSA"
    return key


@pytest.fixture(scope="session")
def rsa_keypair():
    """Generate an RSA 2048 keypair and its did:key.

    Returns a dict with: key, pem_pkcs8, pem_pkcs1, did_key, kid.
    """
    import base58
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    pem_pkcs8 = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pem_pkcs1 = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pkcs1 = key.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.PKCS1,
    )

    did_key = "did:key:z" + base58.b58encode(RSA_MULTICODEC_PREFIX + pub_pkcs1).decode()
    kid = f"{did_key}#{did_key[len('did:key:'):]}"

    return {
        "key": key,
        "pem_pkcs8": pem_pkcs8,
        "pem_pkcs1": pem_pkcs1,
        "did_key": did_key,
        "kid": kid,
    }


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



class TestParseUvarint:
    def test_single_byte_value(self):
        value, used = _parse_uvarint(bytes([0x7F]))
        assert value == 0x7F and used == 1

    def test_two_byte_continuation(self):
        value, used = _parse_uvarint(bytes([0x80, 0x01]))
        assert value == 128 and used == 2

    def test_rsa_multicodec(self):
        value, used = _parse_uvarint(RSA_MULTICODEC_PREFIX)
        assert value == 0x1205 and used == 2

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



class TestLoadPrivateKey:
    def test_pkcs8_pem_bytes_is_rsa(self, rsa_keypair):
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
        key = _load_private_key_bytes(rsa_keypair["pem_pkcs8"])
        assert isinstance(key, RSAPrivateKey)

    def test_pkcs1_pem_bytes_is_rsa(self, rsa_keypair):
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
        key = _load_private_key_bytes(rsa_keypair["pem_pkcs1"])
        assert isinstance(key, RSAPrivateKey)

    def test_der_bytes_is_rsa(self, rsa_keypair):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
        der = rsa_keypair["key"].private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        assert isinstance(_load_private_key_bytes(der), RSAPrivateKey)

    def test_ed25519_pem_bytes_is_ed25519(self):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        pem = Ed25519PrivateKey.generate().private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        assert isinstance(_load_private_key_bytes(pem), Ed25519PrivateKey)

    def test_encrypted_pem_raises(self, rsa_keypair):
        from cryptography.hazmat.primitives import serialization
        pem = rsa_keypair["key"].private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(b"secret"),
        )
        with pytest.raises(ValueError, match="could not be loaded"):
            _load_private_key_bytes(pem)

    def test_unsupported_key_type_raises(self):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        pem = ec.generate_private_key(ec.SECP256R1()).private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        with pytest.raises(ValueError, match="Unsupported private key type"):
            _load_private_key_bytes(pem)

    def test_text_with_real_newlines(self, rsa_keypair):
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
        key = _load_private_key_from_text(rsa_keypair["pem_pkcs8"].decode())
        assert isinstance(key, RSAPrivateKey)

    def test_text_with_literal_backslash_n(self, rsa_keypair):
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
        text = rsa_keypair["pem_pkcs8"].decode().replace("\n", "\\n")
        assert isinstance(_load_private_key_from_text(text), RSAPrivateKey)

    def test_text_bare_base64_body(self, rsa_keypair):
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
        body = "".join(
            line
            for line in rsa_keypair["pem_pkcs8"].decode().splitlines()
            if "-----" not in line
        )
        assert isinstance(_load_private_key_from_text(body), RSAPrivateKey)

    def test_text_garbage_raises(self):
        with pytest.raises(ValueError, match="neither PEM nor base64"):
            _load_private_key_from_text("this is not a key!")


class TestLoadSigningKey:
    def test_multibase_is_eddsa(self, ed25519_keypair):
        priv, _, _ = ed25519_keypair
        _, alg = _load_signing_key(priv, None, None)
        assert alg == "EdDSA"

    def test_rsa_file_is_rs256(self, rsa_keypair, tmp_path):
        path = tmp_path / "rsa.pem"
        path.write_bytes(rsa_keypair["pem_pkcs8"])
        _, alg = _load_signing_key(None, str(path), None)
        assert alg == "RS256"

    def test_rsa_text_is_rs256(self, rsa_keypair):
        _, alg = _load_signing_key(None, None, rsa_keypair["pem_pkcs1"].decode())
        assert alg == "RS256"

    def test_small_rsa_key_rejected(self, tmp_path):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        small = rsa.generate_private_key(public_exponent=65537, key_size=1024)
        path = tmp_path / "small.pem"
        path.write_bytes(
            small.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        with pytest.raises(click.ClickException, match="2048"):
            _load_signing_key(None, str(path), None)

    def test_no_key_option_rejected(self):
        with pytest.raises(click.ClickException, match="exactly one"):
            _load_signing_key(None, None, None)

    def test_two_key_options_rejected(self, ed25519_keypair, rsa_keypair):
        priv, _, _ = ed25519_keypair
        with pytest.raises(click.ClickException, match="exactly one"):
            _load_signing_key(priv, None, rsa_keypair["pem_pkcs8"].decode())

    def test_bad_multibase_raises(self):
        with pytest.raises(click.ClickException, match="Could not load private key"):
            _load_signing_key("zNOT-A-REAL-KEY", None, None)



class TestPublicKeyFromDidKey:
    def test_ed25519_returns_32_bytes(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        pub = _public_key_from_did_key(ED25519_DID_KEY)
        assert isinstance(pub, Ed25519PublicKey)
        assert len(_raw_ed25519(pub)) == 32

    def test_accepts_kid_with_fragment(self):
        from_base = _raw_ed25519(_public_key_from_did_key(ED25519_DID_KEY))
        from_kid = _raw_ed25519(_public_key_from_did_key(ED25519_KID))
        assert from_base == from_kid

    def test_strips_whitespace(self):
        pub = _public_key_from_did_key("  " + ED25519_DID_KEY + "  ")
        assert len(_raw_ed25519(pub)) == 32

    def test_rsa_did_key(self, rsa_keypair):
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
        pub = _public_key_from_did_key(rsa_keypair["did_key"])
        assert isinstance(pub, RSAPublicKey)
        assert pub.public_numbers() == rsa_keypair["key"].public_key().public_numbers()

    def test_rsa_kid_with_fragment(self, rsa_keypair):
        pub = _public_key_from_did_key(rsa_keypair["kid"])
        assert pub.public_numbers() == rsa_keypair["key"].public_key().public_numbers()

    def test_rsa_did_key_starts_with_z4mx(self, rsa_keypair):
        assert rsa_keypair["did_key"].startswith("did:key:z4MX")

    def test_non_did_key_raises(self):
        with pytest.raises(ValueError, match="did:key"):
            _public_key_from_did_key("did:web:example.com")

    def test_unsupported_multicodec_raises(self):
        import base58
        raw = bytes([0x80, 0x24]) + (b"\x00" * 32)  # 0x1200 (P-256), not supported here
        bad_did = "did:key:z" + base58.b58encode(raw).decode()
        with pytest.raises(ValueError, match="Unsupported did:key multicodec"):
            _public_key_from_did_key(bad_did)


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
        with _mock_did_json(doc) as mock_get:
            result = _fetch_did_json("did:web:example.com")

        assert result == doc
        args, kwargs = mock_get.call_args
        assert args[0] == "https://example.com/.well-known/did.json"
        assert "Accept" in kwargs["headers"]

    def test_http_error_propagates(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

        with patch(f"{MODULE}.requests.get", return_value=mock_resp):
            with pytest.raises(requests.HTTPError):
                _fetch_did_json("did:web:example.com")

    def test_non_object_response_raises(self):
        with _mock_did_json(["not", "an", "object"]):
            with pytest.raises(ValueError, match="must be a JSON object"):
                _fetch_did_json("did:web:example.com")

    def test_passes_through_path_segments_in_url(self):
        with _mock_did_json({"verificationMethod": []}) as mock_get:
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

    def _rsa_doc(self, did, vm_id, jwk, vm_type="JsonWebKey2020"):
        return {
            "id": did,
            "verificationMethod": [
                {
                    "id": vm_id,
                    "type": vm_type,
                    "controller": did,
                    "publicKeyJwk": jwk,
                }
            ],
            "authentication": [vm_id],
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
        assert _raw_ed25519(result) == pub

    def test_finds_key_when_vm_id_is_relative(self):
        pub, pub_mb = self._did_web_keypair()
        did = "did:web:example.com"
        kid = f"{did}#key-1"
        doc = self._doc(did, "#key-1", pub_mb)

        result = _public_key_from_did_doc(kid=kid, did_doc=doc)
        assert _raw_ed25519(result) == pub

    def test_raw_32_byte_pub_multibase_accepted(self):
        import base58
        pub, _ = self._did_web_keypair()
        pub_mb = "z" + base58.b58encode(pub).decode()
        did = "did:web:example.com"
        kid = f"{did}#key-1"
        doc = self._doc(did, kid, pub_mb)

        result = _public_key_from_did_doc(kid=kid, did_doc=doc)
        assert _raw_ed25519(result) == pub

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
        assert _raw_ed25519(_public_key_from_did_doc(kid=kid, did_doc=doc)) == pub

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
        assert _raw_ed25519(_public_key_from_did_doc(kid=kid, did_doc=doc)) == pub

    def test_invalid_public_key_multibase_raises(self):
        did = "did:web:example.com"
        kid = f"{did}#key-1"
        doc = self._doc(did, kid, "NOT-Z-PREFIXED")

        with pytest.raises(ValueError, match="publicKeyMultibase"):
            _public_key_from_did_doc(kid=kid, did_doc=doc)

    def test_missing_public_key_raises(self):
        did = "did:web:example.com"
        kid = f"{did}#key-1"
        doc = {"id": did, "verificationMethod": [{"id": kid}]}

        with pytest.raises(ValueError, match="neither an RSA publicKeyJwk"):
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

    def test_rsa_json_web_key_2020(self, rsa_keypair):
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
        public_key = rsa_keypair["key"].public_key()
        did = "did:web:example.com"
        kid = f"{did}#key-2"
        doc = self._rsa_doc(did, kid, _rsa_jwk(public_key, alg="RS256", use="sig"))

        result = _public_key_from_did_doc(kid=kid, did_doc=doc)
        assert isinstance(result, RSAPublicKey)
        assert result.public_numbers() == public_key.public_numbers()

    def test_rsa_relative_vm_id(self, rsa_keypair):
        public_key = rsa_keypair["key"].public_key()
        did = "did:web:example.com"
        doc = self._rsa_doc(did, "#key-2", _rsa_jwk(public_key))

        result = _public_key_from_did_doc(kid=f"{did}#key-2", did_doc=doc)
        assert result.public_numbers() == public_key.public_numbers()

    def test_rsa_wrong_vm_type_raises(self, rsa_keypair):
        did = "did:web:example.com"
        kid = f"{did}#key-2"
        doc = self._rsa_doc(
            did,
            kid,
            _rsa_jwk(rsa_keypair["key"].public_key()),
            vm_type="RsaVerificationKey2018",
        )

        with pytest.raises(ValueError, match="JsonWebKey2020"):
            _public_key_from_did_doc(kid=kid, did_doc=doc)

    def test_rsa_jwk_with_private_part_raises(self, rsa_keypair):
        did = "did:web:example.com"
        kid = f"{did}#key-2"
        doc = self._rsa_doc(did, kid, _rsa_jwk(rsa_keypair["key"].public_key(), d="AAAA"))

        with pytest.raises(ValueError, match="private key material"):
            _public_key_from_did_doc(kid=kid, did_doc=doc)

    def test_picks_rsa_key_from_mixed_doc(self, rsa_keypair):
        _, ed_mb = self._did_web_keypair()
        public_key = rsa_keypair["key"].public_key()
        did = "did:web:example.com"
        doc = {
            "id": did,
            "verificationMethod": [
                {"id": f"{did}#key-1", "type": "Ed25519VerificationKey2020", "publicKeyMultibase": ed_mb},
                {"id": f"{did}#key-2", "type": "JsonWebKey2020", "publicKeyJwk": _rsa_jwk(public_key)},
            ],
        }

        result = _public_key_from_did_doc(kid=f"{did}#key-2", did_doc=doc)
        assert result.public_numbers() == public_key.public_numbers()


class TestResolvePublicKeyForKid:
    def test_did_key_path(self):
        pub = _resolve_public_key_for_kid(ED25519_KID)
        assert len(_raw_ed25519(pub)) == 32

    def test_rsa_did_key_path(self, rsa_keypair):
        pub = _resolve_public_key_for_kid(rsa_keypair["kid"])
        assert pub.public_numbers() == rsa_keypair["key"].public_key().public_numbers()

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

        with _mock_did_json(doc):
            result = _resolve_public_key_for_kid(kid)
        assert _raw_ed25519(result) == pub

    def test_unsupported_did_method_raises(self):
        with pytest.raises(ValueError, match="Unsupported DID method"):
            _resolve_public_key_for_kid("did:ethr:0x123#key-1")



class TestSignPayload:
    def test_returns_three_part_jwt_string(self, ed25519_keypair, ed25519_signing_key, valid_challenge_payload):
        _, _, kid = ed25519_keypair
        token = _sign_payload(ed25519_signing_key, "EdDSA", kid, valid_challenge_payload)
        assert isinstance(token, str)
        assert token.count(".") == 2

    def test_header_includes_alg_typ_kid(self, ed25519_keypair, ed25519_signing_key, valid_challenge_payload):
        _, _, kid = ed25519_keypair
        token = _sign_payload(ed25519_signing_key, "EdDSA", kid, valid_challenge_payload)
        header = _decode_segment(token, 0)
        assert header["alg"] == "EdDSA"
        assert header["typ"] == "JWT"
        assert header["kid"] == kid

    def test_payload_round_trips(self, ed25519_keypair, ed25519_signing_key, valid_challenge_payload):
        _, _, kid = ed25519_keypair
        token = _sign_payload(ed25519_signing_key, "EdDSA", kid, valid_challenge_payload)
        assert _decode_segment(token, 1) == valid_challenge_payload

    def test_rs256_header(self, rsa_keypair, valid_challenge_payload):
        payload = dict(valid_challenge_payload, did=rsa_keypair["kid"])
        token = _sign_payload(rsa_keypair["key"], "RS256", rsa_keypair["kid"], payload)
        header = _decode_segment(token, 0)
        assert header["alg"] == "RS256"
        assert header["typ"] == "JWT"
        assert header["kid"] == rsa_keypair["kid"]

    def test_rs256_signature_is_modulus_length(self, rsa_keypair, valid_challenge_payload):
        token = _sign_payload(rsa_keypair["key"], "RS256", rsa_keypair["kid"], valid_challenge_payload)
        segment = token.split(".")[2]
        signature = base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))
        assert len(signature) == 256  # 2048-bit key



class TestVerifySignatureOnly:
    def test_valid_signature_returns_none(self, ed25519_keypair, ed25519_signing_key, valid_challenge_payload):
        _, _, kid = ed25519_keypair
        token = _sign_payload(ed25519_signing_key, "EdDSA", kid, valid_challenge_payload)
        _verify_signature_only(token, _public_key_from_did_key(kid), "EdDSA")

    def test_tampered_signature_raises(self, ed25519_keypair, ed25519_signing_key, valid_challenge_payload):
        import jwt

        _, _, kid = ed25519_keypair
        token = _sign_payload(ed25519_signing_key, "EdDSA", kid, valid_challenge_payload)

        with pytest.raises(jwt.exceptions.InvalidSignatureError):
            _verify_signature_only(_tamper_signature(token), _public_key_from_did_key(kid), "EdDSA")

    def test_does_not_check_expiry(self, ed25519_keypair, ed25519_signing_key):
        """Even with iat/exp in the past, verification must pass — the
        function exists specifically to verify the signature only."""
        _, _, kid = ed25519_keypair
        payload = {
            "did": ED25519_DID_KEY,
            "challenge": CHALLENGE_UUID,
            "aud": "ce-api",
            "iat": 1,
            "exp": 2,
        }
        token = _sign_payload(ed25519_signing_key, "EdDSA", kid, payload)
        _verify_signature_only(token, _public_key_from_did_key(kid), "EdDSA")

    def test_rs256_valid(self, rsa_keypair, valid_challenge_payload):
        token = _sign_payload(rsa_keypair["key"], "RS256", rsa_keypair["kid"], valid_challenge_payload)
        _verify_signature_only(token, _public_key_from_did_key(rsa_keypair["kid"]), "RS256")

    def test_rs256_tampered_raises(self, rsa_keypair, valid_challenge_payload):
        import jwt

        token = _sign_payload(rsa_keypair["key"], "RS256", rsa_keypair["kid"], valid_challenge_payload)
        with pytest.raises(jwt.exceptions.InvalidSignatureError):
            _verify_signature_only(
                _tamper_signature(token),
                _public_key_from_did_key(rsa_keypair["kid"]),
                "RS256",
            )

    def test_rs256_token_rejected_when_only_eddsa_allowed(self, rsa_keypair, valid_challenge_payload):
        import jwt

        token = _sign_payload(rsa_keypair["key"], "RS256", rsa_keypair["kid"], valid_challenge_payload)
        with pytest.raises(jwt.PyJWTError):
            _verify_signature_only(token, _public_key_from_did_key(rsa_keypair["kid"]), "EdDSA")


class TestAssertSignatureVerifiable:
    def test_passes_for_valid_token(self, ed25519_keypair, ed25519_signing_key, valid_challenge_payload):
        _, _, kid = ed25519_keypair
        token = _sign_payload(ed25519_signing_key, "EdDSA", kid, valid_challenge_payload)
        _assert_signature_verifiable(token, kid, "EdDSA")

    def test_tampered_token_raises_click_exception(
        self, ed25519_keypair, ed25519_signing_key, valid_challenge_payload
    ):
        _, _, kid = ed25519_keypair
        token = _sign_payload(ed25519_signing_key, "EdDSA", kid, valid_challenge_payload)

        with pytest.raises(click.ClickException, match="Signature verification failed"):
            _assert_signature_verifiable(_tamper_signature(token), kid, "EdDSA")

    def test_malformed_token_raises_click_exception(self, ed25519_keypair):
        _, _, kid = ed25519_keypair
        with pytest.raises(click.ClickException, match="JWT verification error"):
            _assert_signature_verifiable("not.a.real.jwt", kid, "EdDSA")

    def test_rs256_passes_for_valid_token(self, rsa_keypair, valid_challenge_payload):
        token = _sign_payload(rsa_keypair["key"], "RS256", rsa_keypair["kid"], valid_challenge_payload)
        _assert_signature_verifiable(token, rsa_keypair["kid"], "RS256")

    def test_rs256_against_ed25519_did_raises(self, rsa_keypair, valid_challenge_payload):
        token = _sign_payload(rsa_keypair["key"], "RS256", ED25519_KID, valid_challenge_payload)
        with pytest.raises(click.ClickException, match="resolves to an Ed25519 key"):
            _assert_signature_verifiable(token, ED25519_KID, "RS256")

    def test_eddsa_against_rsa_did_raises(self, ed25519_signing_key, rsa_keypair, valid_challenge_payload):
        token = _sign_payload(ed25519_signing_key, "EdDSA", rsa_keypair["kid"], valid_challenge_payload)
        with pytest.raises(click.ClickException, match="resolves to an RSA key"):
            _assert_signature_verifiable(token, rsa_keypair["kid"], "EdDSA")

    def test_rs256_did_web(self, rsa_keypair, valid_challenge_payload):
        did = "did:web:example.com"
        kid = f"{did}#key-2"
        doc = {
            "id": did,
            "verificationMethod": [
                {
                    "id": kid,
                    "type": "JsonWebKey2020",
                    "publicKeyJwk": _rsa_jwk(rsa_keypair["key"].public_key(), alg="RS256"),
                }
            ],
            "authentication": [kid],
        }
        token = _sign_payload(rsa_keypair["key"], "RS256", kid, valid_challenge_payload)

        with _mock_did_json(doc):
            _assert_signature_verifiable(token, kid, "RS256")



class TestSignCommand:
    """End-to-end through the click command."""

    def _run(self, args):
        result = CliRunner().invoke(sign_individual_challenge, args)
        return result.exit_code, result.output

    def test_rsa_key_file_signs_rs256(self, rsa_keypair, tmp_path, valid_challenge_payload):
        key_path = tmp_path / "rsa.pem"
        key_path.write_bytes(rsa_keypair["pem_pkcs8"])
        challenge = _write_json(
            tmp_path / "challenge.json",
            dict(valid_challenge_payload, did=rsa_keypair["kid"]),
        )
        out_path = tmp_path / "signed.jwt"

        code, output = self._run(
            ["--private-key-file", str(key_path), "--challenge-file", str(challenge), "-o", str(out_path)]
        )

        assert code == 0, output
        token = out_path.read_text(encoding="utf-8")
        header = _decode_segment(token, 0)
        assert header["alg"] == "RS256"
        assert header["kid"] == rsa_keypair["kid"]

    def test_rsa_key_pem_text_signs_rs256(self, rsa_keypair, tmp_path, valid_challenge_payload):
        challenge = _write_json(
            tmp_path / "challenge.json",
            dict(valid_challenge_payload, did=rsa_keypair["kid"]),
        )

        code, output = self._run(
            ["--private-key-pem", rsa_keypair["pem_pkcs8"].decode(), "--challenge-file", str(challenge)]
        )

        assert code == 0, output

    def test_ed25519_multibase_still_signs_eddsa(self, ed25519_keypair, tmp_path, valid_challenge_payload):
        priv, _, kid = ed25519_keypair
        challenge = _write_json(tmp_path / "challenge.json", dict(valid_challenge_payload, did=kid))
        out_path = tmp_path / "signed.jwt"

        code, output = self._run(
            ["--private-key", priv, "--challenge-file", str(challenge), "-o", str(out_path)]
        )

        assert code == 0, output
        assert _decode_segment(out_path.read_text(encoding="utf-8"), 0)["alg"] == "EdDSA"

    def test_two_key_options_fail(self, ed25519_keypair, rsa_keypair, tmp_path, valid_challenge_payload):
        priv, _, _ = ed25519_keypair
        challenge = _write_json(tmp_path / "challenge.json", valid_challenge_payload)

        code, output = self._run(
            [
                "--private-key", priv,
                "--private-key-pem", rsa_keypair["pem_pkcs8"].decode(),
                "--challenge-file", str(challenge),
            ]
        )

        assert code != 0
        assert "exactly one" in output

    def test_missing_required_field_fails(self, rsa_keypair, tmp_path, valid_challenge_payload):
        payload = dict(valid_challenge_payload, did=rsa_keypair["kid"])
        del payload["exp"]
        challenge = _write_json(tmp_path / "challenge.json", payload)

        code, output = self._run(
            ["--private-key-pem", rsa_keypair["pem_pkcs8"].decode(), "--challenge-file", str(challenge)]
        )

        assert code != 0
        assert "exp" in output