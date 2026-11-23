"""RS256 signing for `ce iir challenge sign --algorithm RS256`.

Signs a CE challenge with an RSA private key (alg=RS256) and verifies the
resulting JWT against the public key resolved from the DID (did:key or did:web).
The Ed25519 path lives in ce.implementations.iir_challenge_sign_ed25519.
The command is ce.iir.challenge.sign.

Key resolution:
  - did:key : multicodec 0x1205 (rsa-pub), PKCS#1 RSAPublicKey DER, base58btc.
              https://github.com/multiformats/multicodec
  - did:web : a JsonWebKey2020 verification method with an RSA publicKeyJwk,
              listed under "authentication" (the same rules the IIR API applies).
"""

from __future__ import annotations

import base64
import binascii
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.parse import quote, unquote

import base58
import click
import jwt
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from jwt.algorithms import RSAAlgorithm
from rich.console import Console

console = Console()
err_console = Console(stderr=True)

ALG = "RS256"
MULTICODEC_RSA_PUB = 0x1205
MIN_RSA_KEY_SIZE_BITS = 2048
VERIFICATION_METHOD_TYPE = "JsonWebKey2020"

# Verification relationships the IIR API accepts for an RSA key.
ACCEPTED_RELATIONSHIPS = ("authentication",)



# Multibase + multicodec helpers

def _parse_uvarint(data: bytes) -> Tuple[int, int]:
    x = 0
    s = 0
    for i, b in enumerate(data):
        x |= (b & 0x7F) << s
        if (b & 0x80) == 0:
            return x, i + 1
        s += 7
    raise ValueError("Invalid varint")


def _decode_multibase_base58btc(z_value: str) -> bytes:
    if not z_value.startswith("z"):
        raise ValueError("Expected multibase base58btc string starting with 'z'")
    return base58.b58decode(z_value[1:])


def _split_did_url(did_url: str) -> Tuple[str, str]:
    """Return (did, fragment) for 'did:...#fragment'; fragment is '' when absent."""
    did_url = did_url.strip()
    did, _, fragment = did_url.partition("#")
    return did, fragment



# Private key loading

def _load_private_key_bytes(data: bytes) -> RSAPrivateKey:
    """Load an unencrypted PEM or DER RSA private key (PKCS#8 or PKCS#1)."""
    try:
        if b"-----BEGIN" in data:
            key = serialization.load_pem_private_key(data, password=None)
        else:
            key = serialization.load_der_private_key(data, password=None)
    except TypeError as e:
        # Raised by cryptography when the key is encrypted and no password was given.
        raise ValueError(f"Private key could not be loaded: {e}") from e

    if not isinstance(key, RSAPrivateKey):
        raise ValueError(
            f"Expected an RSA private key, got {type(key).__name__}. "
            "Use --algorithm Ed25519 for Ed25519 keys."
        )

    return key


def _load_private_key_from_text(text: str) -> RSAPrivateKey:
    """Pasted key: full PEM (real newlines or literal \\n), or just the base64 body."""
    cleaned = text.strip().replace("\\n", "\n")

    if "-----BEGIN" in cleaned:
        return _load_private_key_bytes(cleaned.encode("ascii"))

    body = "".join(cleaned.split())
    try:
        der = base64.b64decode(body, validate=True)
    except (binascii.Error, ValueError) as e:
        raise ValueError("Pasted key is neither PEM nor base64 DER.") from e

    return _load_private_key_bytes(der)


def _load_signing_key(private_key_file: str | None, private_key_pem: str | None) -> RSAPrivateKey:
    if bool(private_key_file) == bool(private_key_pem):
        raise click.ClickException(
            "Give the RSA private key as either a file path or the key text, not both."
        )

    try:
        if private_key_file:
            with open(private_key_file, "rb") as f:
                key = _load_private_key_bytes(f.read())
        else:
            key = _load_private_key_from_text(private_key_pem or "")
    except ValueError as e:
        raise click.ClickException(f"Could not load private key: {e}")

    if key.key_size < MIN_RSA_KEY_SIZE_BITS:
        raise click.ClickException(
            f"RSA key is {key.key_size} bits; at least {MIN_RSA_KEY_SIZE_BITS} bits are required."
        )

    return key



# did:key resolution (offline)

def _public_key_from_did_key(did_or_kid: str) -> RSAPublicKey:
    did, fragment = _split_did_url(did_or_kid)
    if not did.startswith("did:key:"):
        raise ValueError("Not a did:key DID")

    identifier = did[len("did:key:"):]
    if fragment and fragment != identifier:
        raise ValueError("did:key fragment must equal the key identifier")

    raw = _decode_multibase_base58btc(identifier)
    code, n = _parse_uvarint(raw)

    if code != MULTICODEC_RSA_PUB:
        raise ValueError(
            f"did:key multicodec 0x{code:X} is not an RSA public key "
            f"(expected 0x{MULTICODEC_RSA_PUB:X})"
        )

    key_bytes = raw[n:]
    if not key_bytes:
        raise ValueError("did:key has no RSA key bytes")

    try:
        key = serialization.load_der_public_key(key_bytes)
    except ValueError as e:
        raise ValueError(f"did:key RSA key is not valid PKCS#1 DER: {e}") from e

    if not isinstance(key, RSAPublicKey):
        raise ValueError("did:key RSA payload is not an RSA public key")

    # PKCS#1 is required; SubjectPublicKeyInfo would also load, so check the round trip.
    pkcs1 = key.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.PKCS1)
    if pkcs1 != key_bytes:
        raise ValueError("did:key RSA key must be PKCS#1 RSAPublicKey DER")

    return key



# did:web resolution (HTTPS using OS trust)

def _did_web_to_url(did_web: str) -> str:
    """did:web:host[:path...] -> https URL. A percent-encoded port (%3A) is decoded."""
    if not did_web.startswith("did:web:"):
        raise ValueError("Not a did:web DID")

    parts = did_web[len("did:web:"):].split(":")
    host = unquote(parts[0])
    if not host or any(c in host for c in "/?#@"):
        raise ValueError("Invalid did:web host")

    path_parts = [quote(unquote(p), safe="") for p in parts[1:]]
    if any(not p for p in path_parts):
        raise ValueError("Invalid did:web path")

    if not path_parts:
        return f"https://{host}/.well-known/did.json"

    return f"https://{host}/{'/'.join(path_parts)}/did.json"


def _fetch_did_json(did_web: str) -> Dict[str, Any]:
    url = _did_web_to_url(did_web)

    r = requests.get(
        url,
        headers={"Accept": "application/did+json, application/json"},
        timeout=15,
    )
    r.raise_for_status()

    doc = r.json()
    if not isinstance(doc, dict):
        raise ValueError("did.json must be a JSON object")
    return doc


def _normalize(vm_id: str, did: str) -> str:
    return did + vm_id if vm_id.startswith("#") else vm_id


def _find_verification_method(
    did_doc: Dict[str, Any], did: str, kid: str
) -> Tuple[Dict[str, Any] | None, bool]:
    """Return (verification method, listed in an accepted relationship)."""
    found: Dict[str, Any] | None = None
    in_relationship = False

    for relationship in ACCEPTED_RELATIONSHIPS:
        entries = did_doc.get(relationship, [])
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, str) and _normalize(entry, did) == kid:
                in_relationship = True
            elif isinstance(entry, dict) and isinstance(entry.get("id"), str):
                if _normalize(entry["id"], did) == kid:
                    in_relationship = True
                    found = entry

    if found is None:
        vms = did_doc.get("verificationMethod", [])
        if not isinstance(vms, list):
            raise ValueError("verificationMethod must be a list")
        for vm in vms:
            if isinstance(vm, dict) and isinstance(vm.get("id"), str):
                if _normalize(vm["id"], did) == kid:
                    found = vm
                    break

    return found, in_relationship


def _public_key_from_verification_method(vm: Dict[str, Any]) -> RSAPublicKey:
    vm_type = vm.get("type")
    if vm_type != VERIFICATION_METHOD_TYPE:
        raise ValueError(
            f"Verification method type is '{vm_type}', expected '{VERIFICATION_METHOD_TYPE}'"
        )

    jwk = vm.get("publicKeyJwk")
    if not isinstance(jwk, dict):
        raise ValueError("Verification method has no publicKeyJwk")

    if jwk.get("kty") != "RSA":
        raise ValueError(f"publicKeyJwk 'kty' is '{jwk.get('kty')}', expected 'RSA'")

    if "d" in jwk:
        raise ValueError("publicKeyJwk contains private key material ('d')")

    if "alg" in jwk and jwk["alg"] != ALG:
        raise ValueError(f"publicKeyJwk 'alg' is '{jwk['alg']}', expected '{ALG}'")

    if "use" in jwk and jwk["use"] != "sig":
        raise ValueError(f"publicKeyJwk 'use' is '{jwk['use']}', expected 'sig'")

    key = RSAAlgorithm.from_jwk(jwk)
    if not isinstance(key, RSAPublicKey):
        raise ValueError("publicKeyJwk is not an RSA public key")

    return key


def _public_key_from_did_doc(*, kid: str, did_doc: Dict[str, Any]) -> RSAPublicKey:
    did, _ = _split_did_url(kid)
    kid = kid.strip()

    if did_doc.get("id") != did:
        raise ValueError("DID document 'id' does not match the DID")

    vm, in_relationship = _find_verification_method(did_doc, did, kid)

    if vm is None:
        raise ValueError(f"kid not found in did.json: {kid}")

    if not in_relationship:
        raise ValueError(
            f"Verification method '{kid}' is not listed under "
            f"{' or '.join(repr(r) for r in ACCEPTED_RELATIONSHIPS)}"
        )

    return _public_key_from_verification_method(vm)


def _resolve_public_key_for_kid(kid: str) -> RSAPublicKey:
    did, _ = _split_did_url(kid)

    if did.startswith("did:key:"):
        return _public_key_from_did_key(kid)

    if did.startswith("did:web:"):
        return _public_key_from_did_doc(kid=kid, did_doc=_fetch_did_json(did))

    raise ValueError(f"Unsupported DID method: {did}")



# Signing + verification

def _sign_payload(private_key: RSAPrivateKey, kid: str, payload_obj: Dict[str, Any]) -> str:
    headers = {"typ": "JWT", "alg": ALG, "kid": kid}

    token = jwt.encode(
        payload=payload_obj,
        key=private_key,
        algorithm=ALG,
        headers=headers,
    )

    if isinstance(token, bytes):
        token = token.decode("utf-8")

    return token


def _verify_signature_only(token: str, public_key: RSAPublicKey) -> None:
    jwt.decode(
        token,
        key=public_key,
        algorithms=[ALG],
        options={
            "verify_signature": True,
            "verify_aud": False,
            "verify_exp": False,
            "verify_iat": False,
            "verify_nbf": False,
            "verify_iss": False,
        },
    )


def _assert_signature_verifiable(token: str, kid: str) -> None:
    pub_key = _resolve_public_key_for_kid(kid)

    if pub_key.key_size < MIN_RSA_KEY_SIZE_BITS:
        raise click.ClickException(
            f"DID RSA key is {pub_key.key_size} bits; at least "
            f"{MIN_RSA_KEY_SIZE_BITS} bits are required."
        )

    try:
        _verify_signature_only(token, pub_key)
    except jwt.exceptions.InvalidSignatureError as e:
        raise click.ClickException(
            "Signature verification failed (token does not match DID public key)."
        ) from e
    except jwt.PyJWTError as e:
        raise click.ClickException(f"JWT verification error: {e}") from e

    err_console.print(
        "[green]Signature verification: OK[/green] (RS256, matches DID public key)"
    )



# Entry point used by `ce iir challenge sign --algorithm RS256`

def load_private_key_argument(value: str) -> RSAPrivateKey:
    """--private-key for RS256: a path to a PEM/DER key file, or the PEM text itself."""
    value = value.strip()
    if not value:
        raise click.ClickException("--private-key is empty.")

    is_text = "-----BEGIN" in value or "\\n" in value
    if not is_text:
        if is_existing_file(value):
            return _load_signing_key(str(Path(value).expanduser()), None)

        if value.startswith("z") and len(value) < 120:
            raise click.ClickException(
                "This looks like an Ed25519 multibase key. Use --algorithm Ed25519 for Ed25519 keys."
            )

        if not _looks_like_base64(value):
            raise click.ClickException(f"RSA private key file not found: {value}")

    return _load_signing_key(None, value)


def is_existing_file(value: str) -> bool:
    """True when value is the path of an existing file."""
    try:
        return Path(value).expanduser().is_file()
    except OSError:
        # The OS can refuse a value as a path (for example pasted key text that is
        # too long or has characters a path can't have). Such a value is not a file.
        return False


def _looks_like_base64(value: str) -> bool:
    body = "".join(value.split())
    if len(body) < 100:
        return False
    try:
        base64.b64decode(body, validate=True)
    except (binascii.Error, ValueError):
        return False
    return True


def sign_and_verify(private_key_value: str, kid: str, payload_obj: Dict[str, Any]) -> str:
    """Load the RSA key, sign the challenge with RS256, and verify it against the DID."""
    signing_key = load_private_key_argument(private_key_value)

    try:
        token = _sign_payload(signing_key, kid, payload_obj)
    except (ValueError, jwt.PyJWTError) as e:
        raise click.ClickException(f"Signing failed: {e}")

    try:
        _assert_signature_verifiable(token, kid)
    except requests.RequestException as e:
        raise click.ClickException(f"Failed to fetch did.json: {e}")
    except ValueError as e:
        raise click.ClickException(f"DID resolution error: {e}")

    return token
