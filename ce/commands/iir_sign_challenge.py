"""`ce iir challenge sign` - sign and verify a Proof JWT for a single CE challenge.

Reads a challenge JSON file produced by CE, signs it with a private key and
verifies the resulting JWT against the public key resolved from the DID
(did:key or did:web). No login required.

Supported keys (the algorithm follows the key type):
  - Ed25519 -> alg=EdDSA
  - RSA     -> alg=RS256 (2048 bits or more)
"""

from __future__ import annotations

import base64
import binascii
import json
from typing import Any, Dict, Tuple, Union

import base58
import click
import jwt
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
    RSAPublicKey,
)
from jwt.algorithms import RSAAlgorithm
from rich.console import Console

console = Console()
err_console = Console(stderr=True)

ALG_EDDSA = "EdDSA"
ALG_RS256 = "RS256"

MULTICODEC_ED25519_PUB = 0xED
MULTICODEC_ED25519_PRIV = 0x1300
MULTICODEC_RSA_PUB = 0x1205

MIN_RSA_KEY_SIZE_BITS = 2048

PrivateKey = Union[Ed25519PrivateKey, RSAPrivateKey]
PublicKey = Union[Ed25519PublicKey, RSAPublicKey]



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



# Private key

def _extract_ed25519_seed_from_private_key(private_key_multibase: str) -> bytes:
    raw = _decode_multibase_base58btc(private_key_multibase.strip())

    if len(raw) == 32:
        return raw
    if len(raw) == 33 and raw[0] == 0x00:
        return raw[1:]
    if len(raw) == 34 and raw[0] == 0x00 and raw[1] == 0x20:
        return raw[2:]

    code, n = _parse_uvarint(raw)
    if code == MULTICODEC_ED25519_PRIV and len(raw) - n == 32:
        return raw[n:]

    raise ValueError("Unrecognized privateKey encoding")


def _load_private_key_bytes(data: bytes) -> PrivateKey:
    """Load a PEM or DER private key (PKCS#8, or PKCS#1 for RSA). Unencrypted only."""
    try:
        if b"-----BEGIN" in data:
            key = serialization.load_pem_private_key(data, password=None)
        else:
            key = serialization.load_der_private_key(data, password=None)
    except TypeError as e:
        raise ValueError(f"Private key could not be loaded: {e}") from e

    if isinstance(key, (Ed25519PrivateKey, RSAPrivateKey)):
        return key

    raise ValueError(
        f"Unsupported private key type {type(key).__name__}. Expected RSA or Ed25519."
    )


def _load_private_key_from_text(text: str) -> PrivateKey:
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


def _load_signing_key(
    private_key_mb: str | None,
    private_key_file: str | None,
    private_key_pem: str | None,
) -> Tuple[PrivateKey, str]:
    """Return the private key and the JWT alg that goes with it."""
    given = [
        v for v in (private_key_mb, private_key_file, private_key_pem) if v
    ]
    if len(given) != 1:
        raise click.ClickException(
            "Give exactly one of --private-key, --private-key-file or --private-key-pem."
        )

    try:
        if private_key_mb:
            seed = _extract_ed25519_seed_from_private_key(private_key_mb)
            key: PrivateKey = Ed25519PrivateKey.from_private_bytes(seed)
        elif private_key_file:
            with open(private_key_file, "rb") as f:
                key = _load_private_key_bytes(f.read())
        else:
            key = _load_private_key_from_text(private_key_pem or "")
    except ValueError as e:
        raise click.ClickException(f"Could not load private key: {e}")

    if isinstance(key, RSAPrivateKey):
        if key.key_size < MIN_RSA_KEY_SIZE_BITS:
            raise click.ClickException(
                f"RSA key is {key.key_size} bits; at least "
                f"{MIN_RSA_KEY_SIZE_BITS} bits are required."
            )
        return key, ALG_RS256

    return key, ALG_EDDSA



# did:key resolution (offline)

def _public_key_from_did_key(did_or_kid: str) -> PublicKey:
    base = did_or_kid.split("#", 1)[0].strip()
    if not base.startswith("did:key:"):
        raise ValueError("Not a did:key DID")

    mb = base[len("did:key:"):]
    raw = _decode_multibase_base58btc(mb)

    if len(raw) == 32:
        return Ed25519PublicKey.from_public_bytes(raw)

    code, n = _parse_uvarint(raw)
    key_bytes = raw[n:]

    if code == MULTICODEC_ED25519_PUB and len(key_bytes) == 32:
        return Ed25519PublicKey.from_public_bytes(key_bytes)

    if code == MULTICODEC_RSA_PUB:
        # did:key RSA keys are PKCS#1 RSAPublicKey DER.
        key = serialization.load_der_public_key(key_bytes)
        if isinstance(key, RSAPublicKey):
            return key
        raise ValueError("did:key RSA payload is not an RSA public key")

    raise ValueError(
        f"Unsupported did:key multicodec 0x{code:X} (expected Ed25519 or RSA)"
    )



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


def _public_key_from_verification_method(vm: Dict[str, Any]) -> PublicKey:
    jwk = vm.get("publicKeyJwk")
    if isinstance(jwk, dict) and jwk.get("kty") == "RSA":
        if vm.get("type") != "JsonWebKey2020":
            raise ValueError(
                f"RSA verification method type is '{vm.get('type')}', "
                "expected 'JsonWebKey2020'"
            )
        if "d" in jwk:
            raise ValueError("publicKeyJwk contains private key material ('d')")

        key = RSAAlgorithm.from_jwk(jwk)
        if isinstance(key, RSAPublicKey):
            return key
        raise ValueError("publicKeyJwk is not an RSA public key")

    # Ed25519: publicKeyMultibase.
    pkmb = vm.get("publicKeyMultibase")
    if not isinstance(pkmb, str) or not pkmb.startswith("z"):
        raise ValueError(
            "Verification method has neither an RSA publicKeyJwk "
            "nor a valid publicKeyMultibase"
        )

    raw = _decode_multibase_base58btc(pkmb)

    if len(raw) == 32:
        return Ed25519PublicKey.from_public_bytes(raw)

    code, n = _parse_uvarint(raw)
    if code == MULTICODEC_ED25519_PUB and (len(raw) - n) == 32:
        return Ed25519PublicKey.from_public_bytes(raw[n:])

    raise ValueError(
        "publicKeyMultibase is not an Ed25519 key encoding we recognize"
    )


def _public_key_from_did_doc(*, kid: str, did_doc: Dict[str, Any]) -> PublicKey:
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

        return _public_key_from_verification_method(vm)

    raise ValueError(f"kid not found in did.json: {kid}")


def _resolve_public_key_for_kid(kid: str) -> PublicKey:
    base = kid.split("#", 1)[0].strip()

    if base.startswith("did:key:"):
        return _public_key_from_did_key(kid)

    if base.startswith("did:web:"):
        did_doc = _fetch_did_json(base)
        return _public_key_from_did_doc(kid=kid, did_doc=did_doc)

    raise ValueError(f"Unsupported DID method: {base}")



# Signing + verification

def _sign_payload(
    private_key: PrivateKey,
    alg: str,
    kid: str,
    payload_obj: Dict[str, Any],
) -> str:
    headers = {"typ": "JWT", "alg": alg, "kid": kid}

    token = jwt.encode(
        payload=payload_obj,
        key=private_key,
        algorithm=alg,
        headers=headers,
    )

    if isinstance(token, bytes):
        token = token.decode("utf-8")

    return token


def _verify_signature_only(token: str, public_key: PublicKey, alg: str) -> None:
    jwt.decode(
        token,
        key=public_key,
        algorithms=[alg],
        options={
            "verify_signature": True,
            "verify_aud": False,
            "verify_exp": False,
            "verify_iat": False,
            "verify_nbf": False,
            "verify_iss": False,
        },
    )


def _assert_signature_verifiable(token: str, kid: str, alg: str) -> None:
    pub_key = _resolve_public_key_for_kid(kid)

    if alg == ALG_RS256 and not isinstance(pub_key, RSAPublicKey):
        raise click.ClickException(
            "Signed with an RSA key, but the DID resolves to an Ed25519 key."
        )

    if alg == ALG_EDDSA and not isinstance(pub_key, Ed25519PublicKey):
        raise click.ClickException(
            "Signed with an Ed25519 key, but the DID resolves to an RSA key."
        )

    try:
        _verify_signature_only(token, pub_key, alg)
    except jwt.exceptions.InvalidSignatureError as e:
        raise click.ClickException(
            "Signature verification failed (token does not match DID public key)."
        ) from e
    except jwt.PyJWTError as e:
        raise click.ClickException(f"JWT verification error: {e}") from e

    err_console.print(
        f"[green]Signature verification: OK[/green] ({alg}, matches DID public key)"
    )



# Click command

@click.command("sign")
@click.option(
    "--private-key",
    "private_key",
    default=None,
    metavar="MULTIBASE",
    help="Ed25519 private seed (multibase base58btc, starts with 'z').",
)
@click.option(
    "--private-key-file",
    "private_key_file",
    default=None,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    metavar="PATH",
    help="PEM or DER private key file (RSA -> RS256, Ed25519 -> EdDSA). Unencrypted.",
)
@click.option(
    "--private-key-pem",
    "private_key_pem",
    default=None,
    metavar="TEXT",
    help=(
        "Pasted private key: full PEM (newlines or literal \\n) or just the "
        "base64 body. RSA -> RS256, Ed25519 -> EdDSA."
    ),
)
@click.option(
    "--challenge-file",
    "challenge_file",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    metavar="PATH",
    help="Path to CE-generated challenge JSON file.",
)
@click.option(
    "--output", "-o",
    "out_path",
    default=None,
    type=click.Path(dir_okay=False, writable=True),
    metavar="PATH",
    help="Write JWT to this file (otherwise printed to stdout).",
)
def sign_individual_challenge(
    private_key: str | None,
    private_key_file: str | None,
    private_key_pem: str | None,
    challenge_file: str,
    out_path: str | None,
) -> None:
    """Sign a single CE challenge JSON file and produce a Proof JWT.

    \b
    The algorithm follows the key: Ed25519 -> EdDSA, RSA -> RS256.
    Give exactly one of --private-key, --private-key-file, --private-key-pem.
    The challenge JSON must include: did, challenge, aud, iat, exp.
    Signature verification uses did:key (offline) or did:web (HTTPS).

    \b
    Examples:
      ce iir challenge sign --private-key zABC... \\
        --challenge-file challenge.json -o signed-challenge.jwt

    \b
      ce iir challenge sign --private-key-file rsa-key.pem \\
        --challenge-file challenge.json -o signed-challenge.jwt
    """
    signing_key, alg = _load_signing_key(
        private_key,
        private_key_file,
        private_key_pem,
    )

    try:
        with open(challenge_file, "r", encoding="utf-8") as f:
            payload_obj = json.load(f)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Challenge file is not valid JSON: {e}")

    if not isinstance(payload_obj, dict):
        raise click.ClickException("Challenge payload must be a JSON object.")

    required_fields = ["did", "challenge", "aud", "iat", "exp"]
    missing = [k for k in required_fields if k not in payload_obj]
    if missing:
        raise click.ClickException(
            f"Challenge JSON missing required field(s): {', '.join(missing)}"
        )

    did_value = payload_obj.get("did")
    if not isinstance(did_value, str) or not did_value.strip():
        raise click.ClickException(
            'Challenge JSON must include a non-empty string field "did".'
        )

    kid = did_value.strip()

    try:
        token = _sign_payload(signing_key, alg, kid, payload_obj)
    except (ValueError, jwt.PyJWTError) as e:
        raise click.ClickException(f"Signing failed: {e}")

    try:
        _assert_signature_verifiable(token, kid, alg)
    except requests.RequestException as e:
        raise click.ClickException(f"Failed to fetch did.json: {e}")
    except ValueError as e:
        raise click.ClickException(f"DID resolution error: {e}")

    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(token)
        err_console.print(f"Wrote Proof JWT to: [cyan]{out_path}[/cyan]")
    else:
        click.echo(token)