"""API calls and validations"""

from __future__ import annotations

import base64
import json
import re
from typing import Any

import base58
import jwt
import requests
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


CE_GUID_RE = re.compile(
    r"^ce-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

SUPPORTED_ALGORITHMS = {"Ed25519", "secp256k1", "P-256", "X25519"}

DID_KEY_PREFIX_MAP = {
    "z6Mk": "Ed25519",
    "zQ3s": "secp256k1",
    "zDn":  "P-256",
    "z6LS": "X25519",
}

def validate_ctid(ctid: str) -> tuple[bool, str]:
    if not ctid:
        return False, "CTID is empty"
    if CE_GUID_RE.match(ctid):
        return True, ""
    return False, f"CTID '{ctid}' does not match ce-guid format"


def validate_date(value: str, field_name: str) -> tuple[bool, str, str]:
    if not value:
        return True, "", ""
    from datetime import datetime, timezone
    try:
        parsed = datetime.strptime(value, "%m/%d/%Y")
        utc_dt = parsed.replace(tzinfo=timezone.utc)
        iso_value = utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        return True, "", iso_value
    except ValueError:
        return False, f"{field_name} must be in MM/DD/YYYY format, got '{value}'", ""


def classify_did(did: str) -> tuple[str, str]:
    if not did:
        return "unknown", "DID is empty"
    if did.startswith("did:key:"):
        return "did:key", ""
    if did.startswith("did:web:"):
        return "did:web", ""
    return "unknown", f"unrecognised DID method in '{did}'"


def validate_did_key_prefix(did: str, algorithm: str) -> tuple[bool, str]:
    if not algorithm:
        return False, "Algorithm is required for did:key"
    if algorithm not in SUPPORTED_ALGORITHMS:
        return False, f"unsupported algorithm '{algorithm}' — must be one of {', '.join(sorted(SUPPORTED_ALGORITHMS))}"
    key_part = did[len("did:key:"):]
    if not key_part:
        return False, "did:key has no key material after 'did:key:'"
    expected = next(
        (alg for pfx, alg in DID_KEY_PREFIX_MAP.items() if key_part.startswith(pfx)), None
    )
    if expected is None:
        return False, f"unrecognised did:key prefix '{key_part[:8]}...'"
    if expected != algorithm:
        return False, f"algorithm mismatch: key prefix suggests '{expected}' but CSV declares '{algorithm}'"
    return True, ""


def validate_verification_method(vm: str, did: str, api_vm_ids: list[str]) -> tuple[bool, str]:
    if not vm:
        return False, "VerificationMethod is empty"
    if not vm.startswith(did.split("#")[0]):
        return False, f"VerificationMethod '{vm}' does not belong to DID '{did}'"
    if api_vm_ids and vm not in api_vm_ids:
        return False, (
            f"VerificationMethod '{vm}' not found in DID document. "
            f"Valid: {', '.join(api_vm_ids)}"
        )
    return True, ""


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _error_detail(r: requests.Response) -> str:
    try:
        body = r.json()
        return (
            body.get("message")
            or body.get("detail")
            or body.get("title")
            or body.get("Error")
            or r.text
        )
    except Exception:
        return r.text



def call_is_user_member(
    user_id: str, ctid: str, token: str, publisher_base: str, ssl_verify: bool
) -> tuple[bool, str]:
    """GET /api/iir/isUserAMember?userId=...&ctid=...
    Returns { valid: bool }.
    """
    try:
        r = requests.get(
            f"{publisher_base.rstrip('/')}/api/iir/isUserAMember",
            params={"userId": user_id, "ctid": ctid},
            headers=_headers(token),
            timeout=60,
            verify=ssl_verify,
        )
        if not r.ok:
            return False, f"isUserMember error {r.status_code}: {_error_detail(r)}"
        data = r.json()
        if not data.get("valid", False):
            return False, "User is not a member of this organization"
        return True, ""
    except requests.RequestException as e:
        return False, f"isUserMember request failed: {e}"


def call_get_registry_resource(
    ctid: str, token: str, publisher_base: str, ssl_verify: bool
) -> tuple[bool, dict, str]:
    try:
        r = requests.get(
            f"{publisher_base.rstrip('/')}/api/iir/getRegistryResource",
            params={"ctid": ctid},
            headers=_headers(token),
            timeout=60,
            verify=ssl_verify,
        )
        if r.status_code == 400:
            return False, {}, f"Registry lookup failed: {_error_detail(r)}"
        if not r.ok:
            return False, {}, f"Registry API error {r.status_code}: {_error_detail(r)}"
        data = r.json()
        if not data.get("ExistsInRegistry", False):
            return False, {}, f"CTID '{ctid}' not found in registry"
        return True, data, ""
    except requests.RequestException as e:
        return False, {}, f"Registry API request failed: {e}"


def call_validate_did_key(
    did: str, alg: str, token: str, publisher_base: str, ssl_verify: bool
) -> tuple[bool, dict, str]:
    try:
        r = requests.get(
            f"{publisher_base.rstrip('/')}/api/iir/validateDidKey",
            params={"did": did, "alg": alg},
            headers=_headers(token),
            timeout=60,
            verify=ssl_verify,
        )
        if r.status_code == 400:
            return False, {}, f"DID validation failed: {_error_detail(r)}"
        if not r.ok:
            return False, {}, f"validateDidKey error {r.status_code}: {_error_detail(r)}"
        return True, r.json(), ""
    except requests.RequestException as e:
        return False, {}, f"validateDidKey request failed: {e}"


def call_validate_did_web(
    did: str, token: str, publisher_base: str, ssl_verify: bool
) -> tuple[bool, dict, str]:
    try:
        r = requests.get(
            f"{publisher_base.rstrip('/')}/api/iir/validateDidWeb",
            params={"did": did},
            headers=_headers(token),
            timeout=60,
            verify=ssl_verify,
        )
        if r.status_code == 400:
            return False, {}, f"DID validation failed: {_error_detail(r)}"
        if r.status_code == 502:
            return False, {}, "could not fetch remote DID document (502)"
        if not r.ok:
            return False, {}, f"validateDidWeb error {r.status_code}: {_error_detail(r)}"
        return True, r.json(), ""
    except requests.RequestException as e:
        return False, {}, f"validateDidWeb request failed: {e}"


def call_create_challenge(
    ctid: str, vm_id: str, token: str, publisher_base: str, ssl_verify: bool
) -> tuple[bool, dict, str]:
    try:
        r = requests.post(
            f"{publisher_base.rstrip('/')}/api/iir/createChallenges",
            headers=_headers(token),
            json={"Ctid": ctid, "VerificationMethodIds": [vm_id]},
            timeout=60,
            verify=ssl_verify,
        )
        if r.status_code == 400:
            return False, {}, f"createChallenges failed: {_error_detail(r)}"
        if not r.ok:
            return False, {}, f"createChallenges error {r.status_code}: {_error_detail(r)}"
        challenges = r.json()
        if not challenges:
            return False, {}, "createChallenges returned empty array"
        return True, challenges[0], ""
    except requests.RequestException as e:
        return False, {}, f"createChallenges request failed: {e}"



def call_verify_jwt_signature(
    proof_jwt: str, challenge_uuid: str, token: str, publisher_base: str, ssl_verify: bool
) -> tuple[bool, str]:
    try:
        r = requests.post(
            f"{publisher_base.rstrip('/')}/api/iir/validateJwt",
            headers=_headers(token),
            json={"Jwt": proof_jwt, "ChallengeId": challenge_uuid},
            timeout=60,
            verify=ssl_verify,
        )
        if r.status_code == 400:
            return False, f"JWT validation failed: {_error_detail(r)}"
        if r.status_code == 404:
            return False, "Challenge not found (404)"
        if not r.ok:
            return False, f"validateJwt error {r.status_code}: {_error_detail(r)}"
        return True, ""
    except requests.RequestException as e:
        return False, f"validateJwt request failed: {e}"




def call_save_challenge_token(
    ctid: str, challenge_uuid: str, token_jwt: str,
    token: str, publisher_base: str, ssl_verify: bool
) -> tuple[bool, str]:
    try:
        r = requests.post(
            f"{publisher_base.rstrip('/')}/api/iir/saveChallengeToken",
            headers=_headers(token),
            json={"Ctid": ctid, "ChallengeId": challenge_uuid, "Token": token_jwt},
            timeout=60,
            verify=ssl_verify,
        )
        if r.status_code == 400:
            return False, f"saveChallengeToken failed: {_error_detail(r)}"
        if not r.ok:
            return False, f"saveChallengeToken error {r.status_code}: {_error_detail(r)}"
        return True, ""
    except requests.RequestException as e:
        return False, f"saveChallengeToken request failed: {e}"




def call_submit_to_iir(
    ctid: str,
    did: str,
    name: str,
    legal_name: str,
    registry_uri: str,
    subject_web_page: str,
    token: str,
    publisher_base: str,
    ssl_verify: bool,
    logo_uri: str = "",
    logo_base64: str = "",
    valid_from: str = "",
    valid_until: str = "",
) -> tuple[bool, str]:
    try:
        payload = {
            "CTID":                  ctid,
            "DID":                   did,
            "Name":                  name,
            "LegalName":             legal_name,
            "CredentialRegistryUri": registry_uri,
            "SubjectWebPage":        subject_web_page,
            "LogoBase64":            logo_base64 or None,
            "LogoUri":               logo_uri or None,
        }
        if valid_from:
            payload["ValidFrom"] = valid_from
        if valid_until:
            payload["ValidUntil"] = valid_until

        r = requests.post(
            f"{publisher_base.rstrip('/')}/api/iir/submitToIIR",
            headers=_headers(token),
            json=payload,
            timeout=60,
            verify=ssl_verify,
        )
        if r.status_code == 409:
            return False, "Did already exists (409)"
        if r.status_code == 400:
            return False, f"submitToIIR failed: {_error_detail(r)}"
        if not r.ok:
            return False, f"submitToIIR error {r.status_code}: {_error_detail(r)}"
        return True, ""
    except requests.RequestException as e:
        return False, f"submitToIIR request failed: {e}"




def _parse_uvarint(data: bytes) -> tuple[int, int]:
    x, s = 0, 0
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


def _extract_ed25519_seed(private_key_multibase: str) -> bytes:
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
    raise ValueError("Invalid did:key encoding")


def _did_web_to_url(did_web: str) -> str:
    method_specific = did_web[len("did:web:"):]
    parts = method_specific.split(":")
    host = parts[0]
    path_parts = parts[1:]
    if not path_parts:
        return f"https://{host}/.well-known/did.json"
    return f"https://{host}/{'/'.join(path_parts)}/did.json"


def _fetch_did_json(did_web_base: str) -> dict:
    url = _did_web_to_url(did_web_base)
    r = requests.get(
        url, headers={"Accept": "application/did+json, application/json"}, timeout=15
    )
    r.raise_for_status()
    doc = r.json()
    if not isinstance(doc, dict):
        raise ValueError("did.json must be a JSON object")
    return doc


def _public_key_from_did_doc(*, kid: str, did_doc: dict) -> bytes:
    did_base = kid.split("#", 1)[0].strip()
    kid = kid.strip()
    vms = did_doc.get("verificationMethod", [])

    def normalize(vm_id: str) -> str:
        return did_base + vm_id if vm_id.startswith("#") else vm_id

    for vm in vms:
        if not isinstance(vm, dict):
            continue
        if normalize(vm.get("id", "")) != kid:
            continue
        pkmb = vm.get("publicKeyMultibase", "")
        if not isinstance(pkmb, str) or not pkmb.startswith("z"):
            raise ValueError("Invalid publicKeyMultibase")
        raw = _decode_multibase_base58btc(pkmb)
        if len(raw) == 32:
            return raw
        code, n = _parse_uvarint(raw)
        if code == 0xED and (len(raw) - n) == 32:
            return raw[n:]
        raise ValueError("publicKeyMultibase is not an Ed25519 key we recognise")
    raise ValueError(f"kid not found in did.json: {kid}")


def _resolve_public_key_bytes(kid: str) -> bytes:
    base = kid.split("#", 1)[0].strip()
    if base.startswith("did:key:"):
        return _extract_ed25519_pub_from_did_key(kid)
    if base.startswith("did:web:"):
        return _public_key_from_did_doc(kid=kid, did_doc=_fetch_did_json(base))
    raise ValueError(f"Unsupported DID method: {base}")


def sign_proof_jwt(private_key_multibase: str, kid: str, payload_obj: dict) -> str:
    seed = _extract_ed25519_seed(private_key_multibase)
    private_key = Ed25519PrivateKey.from_private_bytes(seed)
    token = jwt.encode(
        payload=payload_obj,
        key=private_key,
        algorithm="EdDSA",
        headers={"typ": "JWT", "alg": "EdDSA", "kid": kid},
    )
    return token if isinstance(token, str) else token.decode("utf-8")


def verify_proof_jwt(token: str, kid: str) -> tuple[bool, str]:
    try:
        pub_bytes = _resolve_public_key_bytes(kid)
        pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)
        jwt.decode(
            token, key=pub_key, algorithms=["EdDSA"],
            options={"verify_signature": True, "verify_aud": False,
                     "verify_exp": False, "verify_iat": False,
                     "verify_nbf": False, "verify_iss": False},
        )
        return True, ""
    except jwt.exceptions.InvalidSignatureError:
        return False, "signature verification failed — private key does not match verification method"
    except jwt.PyJWTError as e:
        return False, f"JWT error: {e}"
    except Exception as e:
        return False, f"verification error: {e}"




def extract_user_id_from_token(access_token: str) -> str:
    import uuid
    try:
        payload_part = access_token.split(".")[1]
        padding = 4 - len(payload_part) % 4
        payload_part += "=" * (padding % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload_part))
        user_id = decoded.get("sub", "")
        if not user_id:
            raise ValueError("'sub' claim missing from token")
        try:
            uuid.UUID(user_id)
        except ValueError:
            raise ValueError(f"'sub' claim '{user_id}' is not a valid GUID")
        return user_id
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Failed to extract userId from token: {e}") from e