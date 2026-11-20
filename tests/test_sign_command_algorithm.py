"""
Unit tests for `ce iir challenge sign --algorithm Ed25519|RS256`.
Run with:
    pytest -m unit -s
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner



pytestmark = pytest.mark.unit


from ce.commands.iir_sign_challenge import sign_individual_challenge


RS256_MODULE = "ce.commands.iir_sign_challenge_rs256"

CHALLENGE_UUID = "11111111-2222-3333-4444-555555555555"
CTID = "ce-12345678-1234-1234-1234-123456789abc"
DID_WEB = "did:web:example.com"
DID_WEB_KID = f"{DID_WEB}#key-1"



# Helpers

def _run(args):
    result = CliRunner().invoke(sign_individual_challenge, args)
    return result.exit_code, result.output


def _decode_segment(token: str, index: int) -> dict:
    segment = token.split(".")[index]
    return json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))


def _write_challenge(tmp_path: Path, did: str) -> Path:
    path = tmp_path / "challenge.json"
    path.write_text(
        json.dumps(
            {
                "did": did,
                "challenge": CHALLENGE_UUID,
                "aud": "ce-api",
                "iat": 1700000000,
                "exp": 1700003600,
                "ctid": CTID,
            }
        ),
        encoding="utf-8",
    )
    return path


def _b64url_uint(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()



# Fixtures

@pytest.fixture(scope="session")
def ed25519_keys():
    """(private multibase seed, did:key kid) for a fresh Ed25519 key."""
    import base58
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    sk = Ed25519PrivateKey.generate()
    seed = sk.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    pub = sk.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    did = "did:key:z" + base58.b58encode(bytes([0xED, 0x01]) + pub).decode()

    return "z" + base58.b58encode(seed).decode(), f"{did}#{did[len('did:key:'):]}"


@pytest.fixture(scope="session")
def rsa_key():
    from cryptography.hazmat.primitives.asymmetric import rsa

    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="session")
def rsa_kid(rsa_key):
    import base58
    from cryptography.hazmat.primitives import serialization

    pkcs1 = rsa_key.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.PKCS1)
    did = "did:key:z" + base58.b58encode(bytes([0x85, 0x24]) + pkcs1).decode()
    return f"{did}#{did[len('did:key:'):]}"


@pytest.fixture
def rsa_pem_text(rsa_key) -> str:
    from cryptography.hazmat.primitives import serialization

    return rsa_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


@pytest.fixture
def rsa_pem_file(rsa_pem_text, tmp_path) -> Path:
    path = tmp_path / "rsa-key.pem"
    path.write_text(rsa_pem_text, encoding="ascii")
    return path



class TestAlgorithmOption:
    def test_algorithm_is_required(self, ed25519_keys, tmp_path):
        priv, kid = ed25519_keys
        code, output = _run(["--private-key", priv, "--challenge-file", str(_write_challenge(tmp_path, kid))])

        assert code != 0
        assert "--algorithm" in output

    @pytest.mark.parametrize("value", ["rs256", "ed25519", "EdDSA", "RSA", "HS256"])
    def test_only_exact_values_accepted(self, ed25519_keys, tmp_path, value):
        priv, kid = ed25519_keys
        code, output = _run(
            ["--algorithm", value, "--private-key", priv, "--challenge-file", str(_write_challenge(tmp_path, kid))]
        )

        assert code != 0
        assert "Invalid value for '--algorithm'" in output

    def test_help_lists_both_algorithms(self):
        code, output = _run(["--help"])

        assert code == 0
        assert "Ed25519" in output and "RS256" in output



class TestEd25519:
    def test_signs_eddsa(self, ed25519_keys, tmp_path):
        priv, kid = ed25519_keys
        out_path = tmp_path / "signed.jwt"

        code, output = _run(
            [
                "--algorithm", "Ed25519",
                "--private-key", priv,
                "--challenge-file", str(_write_challenge(tmp_path, kid)),
                "-o", str(out_path),
            ]
        )

        assert code == 0, output
        assert _decode_segment(out_path.read_text(encoding="utf-8"), 0) == {"typ": "JWT", "alg": "EdDSA", "kid": kid}

    def test_rsa_pem_file_gets_hint(self, rsa_pem_file, ed25519_keys, tmp_path):
        _, kid = ed25519_keys
        code, output = _run(
            [
                "--algorithm", "Ed25519",
                "--private-key", str(rsa_pem_file),
                "--challenge-file", str(_write_challenge(tmp_path, kid)),
            ]
        )

        assert code != 0
        assert "--algorithm RS256" in output

    def test_rsa_pem_text_gets_hint(self, rsa_pem_text, ed25519_keys, tmp_path):
        _, kid = ed25519_keys
        code, output = _run(
            [
                "--algorithm", "Ed25519",
                "--private-key", rsa_pem_text,
                "--challenge-file", str(_write_challenge(tmp_path, kid)),
            ]
        )

        assert code != 0
        assert "--algorithm RS256" in output



class TestRs256:
    def test_pem_file_did_key(self, rsa_pem_file, rsa_kid, tmp_path):
        out_path = tmp_path / "signed.jwt"

        code, output = _run(
            [
                "--algorithm", "RS256",
                "--private-key", str(rsa_pem_file),
                "--challenge-file", str(_write_challenge(tmp_path, rsa_kid)),
                "-o", str(out_path),
            ]
        )

        assert code == 0, output
        assert _decode_segment(out_path.read_text(encoding="utf-8"), 0) == {"typ": "JWT", "alg": "RS256", "kid": rsa_kid}

    def test_pem_text_did_web(self, rsa_key, rsa_pem_text, tmp_path):
        numbers = rsa_key.public_key().public_numbers()
        doc = {
            "id": DID_WEB,
            "verificationMethod": [
                {
                    "id": DID_WEB_KID,
                    "type": "JsonWebKey2020",
                    "controller": DID_WEB,
                    "publicKeyJwk": {"kty": "RSA", "n": _b64url_uint(numbers.n), "e": _b64url_uint(numbers.e)},
                }
            ],
            "authentication": [DID_WEB_KID],
        }
        response = MagicMock()
        response.json.return_value = doc
        response.raise_for_status = MagicMock()

        with patch(f"{RS256_MODULE}.requests.get", return_value=response):
            code, output = _run(
                [
                    "--algorithm", "RS256",
                    "--private-key", rsa_pem_text,
                    "--challenge-file", str(_write_challenge(tmp_path, DID_WEB_KID)),
                ]
            )

        assert code == 0, output
        token = output.strip().splitlines()[-1]
        assert _decode_segment(token, 0)["kid"] == DID_WEB_KID

    def test_ed25519_seed_gets_hint(self, ed25519_keys, rsa_kid, tmp_path):
        priv, _ = ed25519_keys
        code, output = _run(
            [
                "--algorithm", "RS256",
                "--private-key", priv,
                "--challenge-file", str(_write_challenge(tmp_path, rsa_kid)),
            ]
        )

        assert code != 0
        assert "--algorithm Ed25519" in output

    def test_missing_pem_file(self, rsa_kid, tmp_path):
        code, output = _run(
            [
                "--algorithm", "RS256",
                "--private-key", str(tmp_path / "missing.pem"),
                "--challenge-file", str(_write_challenge(tmp_path, rsa_kid)),
            ]
        )

        assert code != 0
        assert "RSA private key file not found" in output

    def test_rsa_key_with_ed25519_did(self, rsa_pem_file, ed25519_keys, tmp_path):
        _, kid = ed25519_keys
        code, output = _run(
            [
                "--algorithm", "RS256",
                "--private-key", str(rsa_pem_file),
                "--challenge-file", str(_write_challenge(tmp_path, kid)),
            ]
        )

        assert code != 0
        assert "not an RSA public key" in output

    def test_missing_required_field(self, rsa_pem_file, rsa_kid, tmp_path):
        path = tmp_path / "challenge.json"
        path.write_text(json.dumps({"did": rsa_kid, "challenge": CHALLENGE_UUID, "aud": "ce-api", "iat": 1}), encoding="utf-8")

        code, output = _run(["--algorithm", "RS256", "--private-key", str(rsa_pem_file), "--challenge-file", str(path)])

        assert code != 0
        assert "exp" in output
