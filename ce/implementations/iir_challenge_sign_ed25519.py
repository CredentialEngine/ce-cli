"""Ed25519 signing for `ce iir challenge sign --algorithm Ed25519`.

Signs a CE challenge with an Ed25519 private key (alg=EdDSA) and verifies the
resulting JWT against the public key resolved from the DID (did:key or did:web).
The RS256 path lives in ce.implementations.iir_challenge_sign_rs256.
The command is ce.iir.challenge.sign.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

import base58
import click
import jwt
import requests
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from ce.utils.display import new_console

console = new_console()
err_console = new_console(stderr=True)



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



# Private key to Ed25519 seed


def _extract_ed25519_seed_from_private_key(private_key_multibase: str) -> bytes:
    raw = _decode_multibase_base58btc(private_key_multibase.strip())

    if len(raw) == 32:
        return raw
    if len(raw) == 33 and raw[0] == 0x00:
        return raw[1:]
    if len(raw) == 34 and raw[0] == 0x00 and raw[1] == 0x20:
        return raw[2:]

    code, n = _parse_uvarint(raw)
    if code == 0x1300 and len(raw) - n == 32:
        return raw[n:]

    raise ValueError("Unrecognized privateKey encoding")



# did:key resolution (offline)

def _extract_ed25519_pub_from_did_key(did_or_kid: str) -> bytes:
    base = did_or_kid.split("#", 1)[0].strip()
    if not base.startswith("did:key:"):
        raise ValueError("Not a did:key DID")

    mb = base[len("did:key:"):]
    raw = _decode_multibase_base58btc(mb)

    if len(raw) == 32:
        return raw

    code, n = _parse_uvarint(raw)
    if code == 0xED and (len(raw) - n) == 32:
        return raw[n:]

    raise ValueError("Invalid did:key encoding (expected Ed25519 public key)")



# did:web resolution (HTTPS using OS trust)

def _did_web_to_url(did_web: str) -> str:
    if not did_web.startswith("did:web:"):
        raise ValueError("Not a did:web DID")

    method_specific = did_web[len("did:web:"):]
    parts = method_specific.split(":")
    host = parts[0]
    path_parts = parts[1:]

    if not path_parts:
        return f"https://{host}/.well-known/did.json"

    return f"https://{host}/{'/'.join(path_parts)}/did.json"


def _fetch_did_json(did_web_base: str) -> Dict[str, Any]:
    url = _did_web_to_url(did_web_base)

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


def _public_key_from_did_doc(*, kid: str, did_doc: Dict[str, Any]) -> bytes:
    did_base = kid.split("#", 1)[0].strip()
    kid = kid.strip()

    vms = did_doc.get("verificationMethod", [])
    if not isinstance(vms, list):
        raise ValueError("verificationMethod must be a list")

    def normalize(vm_id: str) -> str:
        return did_base + vm_id if vm_id.startswith("#") else vm_id

    for vm in vms:
        if not isinstance(vm, dict):
            continue
        vm_id = vm.get("id")
        if not isinstance(vm_id, str):
            continue

        if normalize(vm_id) != kid:
            continue

        pkmb = vm.get("publicKeyMultibase")
        if not isinstance(pkmb, str) or not pkmb.startswith("z"):
            raise ValueError("Invalid publicKeyMultibase")

        raw = _decode_multibase_base58btc(pkmb)

        if len(raw) == 32:
            return raw

        code, n = _parse_uvarint(raw)
        if code == 0xED and (len(raw) - n) == 32:
            return raw[n:]

        raise ValueError(
            "publicKeyMultibase is not an Ed25519 key encoding we recognize"
        )

    raise ValueError(f"kid not found in did.json: {kid}")


def _resolve_public_key_bytes_for_kid(kid: str) -> bytes:
    base = kid.split("#", 1)[0].strip()

    if base.startswith("did:key:"):
        return _extract_ed25519_pub_from_did_key(kid)

    if base.startswith("did:web:"):
        did_doc = _fetch_did_json(base)
        return _public_key_from_did_doc(kid=kid, did_doc=did_doc)

    raise ValueError(f"Unsupported DID method: {base}")



# Signing + verification

def _sign_payload(private_key_mb: str, kid: str, payload_obj: Dict[str, Any]) -> str:
    seed = _extract_ed25519_seed_from_private_key(private_key_mb)
    private_key = Ed25519PrivateKey.from_private_bytes(seed)

    headers = {"typ": "JWT", "alg": "EdDSA", "kid": kid}

    token = jwt.encode(
        payload=payload_obj,
        key=private_key,
        algorithm="EdDSA",
        headers=headers,
    )

    if isinstance(token, bytes):
        token = token.decode("utf-8")

    return token


def _verify_signature_only(token: str, public_key: Ed25519PublicKey) -> None:
    jwt.decode(
        token,
        key=public_key,
        algorithms=["EdDSA"],
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
    pub_bytes = _resolve_public_key_bytes_for_kid(kid)
    pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)

    try:
        _verify_signature_only(token, pub_key)
    except jwt.exceptions.InvalidSignatureError as e:
        raise click.ClickException(
            "Signature verification failed (token does not match DID public key)."
        ) from e
    except jwt.PyJWTError as e:
        raise click.ClickException(f"JWT verification error: {e}") from e

    err_console.print(
        "Signature verification: OK (matches DID public key)"
    )



# Entry point used by `ce iir challenge sign --algorithm Ed25519`

def sign_and_verify(private_key_value: str, kid: str, payload_obj: Dict[str, Any]) -> str:
    """Sign the challenge with the Ed25519 seed (EdDSA) and verify it against the DID."""
    try:
        token = _sign_payload(private_key_value, kid, payload_obj)
    except ValueError as e:
        raise click.ClickException(f"Signing failed: {e}")

    try:
        _assert_signature_verifiable(token, kid)
    except requests.RequestException as e:
        raise click.ClickException(f"Failed to fetch did.json: {e}")
    except ValueError as e:
        raise click.ClickException(f"DID resolution error: {e}")

    return token
