"""API calls and validations"""

from __future__ import annotations

import base64
from datetime import timezone
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import base58
import jwt
import requests
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from ce.iir.api.iir_client import AuthenticatedClient
from ce.iir.api.iir_client.models.create_challenges_request import CreateChallengesRequest
from ce.iir.api.iir_client.models.save_challenge_token_request import SaveChallengeTokenRequest
from ce.iir.api.iir_client.models.validate_jwt_request import ValidateJwtRequest
from ce.iir.api.iir_client.models.pub_issuer_dto import PubIssuerDTO

from ce.iir.api.iir_client.api.iir_api.iir_api_is_user_a_member import sync_detailed as is_user_member_sync
from ce.iir.api.iir_client.api.iir_api.iir_api_get_registry_resource import sync_detailed as get_registry_resource_sync
from ce.iir.api.iir_client.api.iir_api.iir_api_get_organization_iir_detail import sync_detailed as get_organization_iir_detail_sync
from ce.iir.api.iir_client.api.iir_api.iir_api_validate_key import sync_detailed as validate_did_key_sync
from ce.iir.api.iir_client.api.iir_api.iir_api_validate_web import sync_detailed as validate_did_web_sync
from ce.iir.api.iir_client.api.iir_api.iir_api_create_challenges import sync_detailed as create_challenges_sync
from ce.iir.api.iir_client.api.iir_api.iir_api_validate_jwt_signature import sync_detailed as validate_jwt_sync
from ce.iir.api.iir_client.api.iir_api.iir_api_save_challenge_token import sync_detailed as save_challenge_token_sync
from ce.iir.api.iir_client.api.iir_api.iir_api_submit_to_iir import sync_detailed as submit_to_iir_sync
from ce.iir.api.iir_client.types import UNSET

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

IIR_TASK = "IIR"

def _client(token: str, base_url: str, ssl_verify: bool) -> AuthenticatedClient:
    return AuthenticatedClient(
        base_url=base_url.rstrip("/"),
        token=token,
        verify_ssl=ssl_verify,
        timeout=60.0,
    )


def _parsed_to_dict(parsed: Any) -> dict:
   
    if not parsed:
        return {}
    if isinstance(parsed, dict):
        return parsed
    if hasattr(parsed, "to_dict"):
        try:
            d = parsed.to_dict()
            if isinstance(d, dict):
                return d
        except Exception:
            pass
    return getattr(parsed, "additional_properties", {}) or {}


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
        parsed = datetime.strptime(value, "%Y-%m-%d")
        utc_dt = parsed.replace(hour=0, minute=0, second=0, tzinfo=timezone.utc)
        iso_value = utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        return True, "", iso_value
    except ValueError:
        return False, f"{field_name} must be in YYYY-MM-DD format, got '{value}'", ""


def validate_date_range(valid_from: str, valid_until: str) -> tuple[bool, str]:
    """Mirror the React page's both-or-neither + vu > vf cross-check.

    Inputs are the raw user values (any format accepted by validate_date).
    """
    vf = (valid_from or "").strip()
    vu = (valid_until or "").strip()

    if not vf and not vu:
        return True, ""
    if bool(vf) != bool(vu):
        return False, "If you provide dates, both Valid From and Valid Until are required."

    ok_vf, err_vf, iso_vf = validate_date(vf, "Valid From")
    if not ok_vf:
        return False, err_vf
    ok_vu, err_vu, iso_vu = validate_date(vu, "Valid Until")
    if not ok_vu:
        return False, err_vu

    if iso_vu <= iso_vf:
        return False, "Valid Until must be after Valid From."
    return True, ""


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


def call_is_user_member(
    user_id, ctid, token, publisher_base, ssl_verify, task: str = IIR_TASK
) -> tuple[bool, str]:
    try:
        client = _client(token, publisher_base, ssl_verify)
        response = is_user_member_sync(user_id, client=client, task=task, ctid=ctid)

        data = _parsed_to_dict(response.parsed)
        valid = data.get("valid", False)
        if not valid:
            return False, "User is not a member of this organization"

        return True, ""

    except Exception as e:
        return False, f"isUserMember request failed: {e}"

def call_get_registry_resource(ctid, token, publisher_base, ssl_verify) -> tuple[bool, dict, str]:
    try:
        client = _client(token, publisher_base, ssl_verify)
        response = get_registry_resource_sync(client=client, ctid=ctid)

        data = _parsed_to_dict(response.parsed)
        exists = data.get("ExistsInRegistry", False)
        if not exists:
            return False, data, f"CTID '{ctid}' not found in registry"

        return True, data, ""

    except Exception as e:
        return False, {}, f"Registry API request failed: {e}"


def call_get_organization_iir_detail(
    ctid, token, publisher_base, ssl_verify
) -> tuple[bool, dict, str]:
    try:
        client = _client(token, publisher_base, ssl_verify)
        response = get_organization_iir_detail_sync(client=client, ctid=ctid)

        envelope = _parsed_to_dict(response.parsed)
        if not envelope:
            return False, {}, "getOrganizationIIRDetail returned empty"

        if not envelope.get("valid", False):
            return False, envelope, "Organization IIR detail not available"

        inner = envelope.get("data") or {}
        if not isinstance(inner, dict):
            inner = {}

        return True, inner, ""

    except Exception as e:
        return False, {}, f"getOrganizationIIRDetail request failed: {e}"


def merge_autofill(registry: dict, accounts: dict) -> dict:
   
    name = registry.get("Name", "") or ""
    registry_uri = registry.get("CredentialRegistryUri", "") or ""
    subject_webpage = registry.get("SubjectWebpage", "") or ""
    image = registry.get("Image", "") or ""
    legal_name = registry.get("LegalName", "") or ""
    logo_base64 = registry.get("LogoBase64", "") or ""

    if accounts:
        if accounts.get("LegalName"):
            legal_name = accounts["LegalName"]
        if not image and accounts.get("LogoUrl"):
            image = accounts["LogoUrl"]

    return {
        "name": name,
        "legal_name": legal_name,
        "registry_uri": registry_uri,
        "subject_webpage": subject_webpage,
        "image": image,
        "logo_base64": logo_base64,
    }


def call_validate_did_key(
    did: str, alg: str, token: str, publisher_base: str, ssl_verify: bool
) -> tuple[bool, dict, str]:
    try:
        client = _client(token, publisher_base, ssl_verify)

        response = validate_did_key_sync(
            client=client,
            did=did,
            alg=alg,
        )

        if response.status_code == 400:
            return False, {}, "DID validation failed"
        if response.status_code >= 400:
            return False, {}, f"validateDidKey error {response.status_code}"

        return True, _parsed_to_dict(response.parsed), ""

    except Exception as e:
        return False, {}, f"validateDidKey request failed: {e}"


def call_validate_did_web(
    did: str, token: str, publisher_base: str, ssl_verify: bool
) -> tuple[bool, dict, str]:
    try:
        client = _client(token, publisher_base, ssl_verify)

        response = validate_did_web_sync(
            client=client,
            did=did,
        )

        if response.status_code == 400:
            return False, {}, "DID validation failed"
        if response.status_code == 502:
            return False, {}, "could not fetch remote DID document (502)"
        if response.status_code >= 400:
            return False, {}, f"validateDidWeb error {response.status_code}"

        return True, _parsed_to_dict(response.parsed), ""

    except Exception as e:
        return False, {}, f"validateDidWeb request failed: {e}"


def call_validate_did(
    did: str, alg: str, token: str, publisher_base: str, ssl_verify: bool
) -> tuple[bool, list[str], dict, str]:
   
    kind, kind_err = classify_did(did)
    if kind == "unknown":
        return False, [], {}, kind_err or "Unsupported DID method"

    if kind == "did:key":
        ok_pfx, err_pfx = validate_did_key_prefix(did, alg)
        if not ok_pfx:
            return False, [], {}, err_pfx
        ok, data, err = call_validate_did_key(did, alg, token, publisher_base, ssl_verify)
    else:
        ok, data, err = call_validate_did_web(did, token, publisher_base, ssl_verify)

    if not ok:
        return False, [], data, err

    vm_ids = data.get("VerificationMethodIds") or []
    if not isinstance(vm_ids, list):
        vm_ids = []
    return True, vm_ids, data, ""


def call_create_challenges(
    ctid: str, vm_ids: list[str], token: str, publisher_base: str, ssl_verify: bool
) -> tuple[bool, list[dict], str]:
    if not vm_ids:
        return False, [], "no verification methods to challenge"

    try:
        client = _client(token, publisher_base, ssl_verify)

        body = CreateChallengesRequest(
            ctid=ctid,
            verification_method_ids=vm_ids,
        )

        response = create_challenges_sync(
            client=client,
            body=body,
        )

        if response.status_code == 400:
            return False, [], "createChallenges failed"
        if response.status_code >= 400:
            return False, [], f"createChallenges error {response.status_code}"

        data = response.parsed
        if not data:
            return False, [], "createChallenges returned empty"

        if isinstance(data, list):
            items = [c.to_dict() if hasattr(c, "to_dict") else dict(c) for c in data]
            return True, items, ""

        single = data.to_dict() if hasattr(data, "to_dict") else None
        if isinstance(single, dict):
            return True, [single], ""

        return False, [], "createChallenges returned unexpected shape"

    except Exception as e:
        return False, [], f"createChallenges request failed: {e}"


def call_verify_jwt_signature(
    proof_jwt: str, challenge_uuid: str, token: str, publisher_base: str, ssl_verify: bool
) -> tuple[bool, str]:
    try:
        client = _client(token, publisher_base, ssl_verify)

        body = ValidateJwtRequest(
            jwt=proof_jwt,
            challenge_id=challenge_uuid,
        )

        response = validate_jwt_sync(
            client=client,
            body=body,
        )

        if response.status_code == 400:
            return False, "JWT validation failed"
        if response.status_code == 404:
            return False, "Challenge not found"
        if response.status_code >= 400:
            return False, f"validateJwt error {response.status_code}"

        return True, ""

    except Exception as e:
        return False, f"validateJwt request failed: {e}"


def call_save_challenge_token(
    ctid: str, challenge_uuid: str, token_jwt: str,
    token: str, publisher_base: str, ssl_verify: bool
) -> tuple[bool, str]:
    try:
        client = _client(token, publisher_base, ssl_verify)

        body = SaveChallengeTokenRequest(
            ctid=ctid,
            challenge_id=challenge_uuid,
            token=token_jwt,
        )

        response = save_challenge_token_sync(
            client=client,
            body=body,
        )

        if response.status_code == 400:
            return False, "saveChallengeToken failed"
        if response.status_code >= 400:
            return False, f"saveChallengeToken error {response.status_code}"

        return True, ""

    except Exception as e:
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
    from datetime import datetime

    def _to_iso_z(value: str) -> str:
        if not value:
            return ""
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            try:
                dt = datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                return ""
        local_midnight = datetime(dt.year, dt.month, dt.day).astimezone()
        return local_midnight.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        client = _client(token, publisher_base, ssl_verify)

        body = PubIssuerDTO(
            ctid=ctid,
            did=did,
            name=name,
            legal_name=legal_name,
            credential_registry_uri=registry_uri,
            subject_web_page=subject_web_page,
            logo_base_64=logo_base64 if logo_base64 else UNSET,
            logo_uri=logo_uri if logo_uri else UNSET,
        )

        df = _to_iso_z(valid_from)
        du = _to_iso_z(valid_until)
        if df:
            body.additional_properties["DateValidFrom"] = df
        if du:
            body.additional_properties["DateValidUntil"] = du

        response = submit_to_iir_sync(client=client, body=body)

        if response.status_code == 409:
            return False, "Did already exists"
        if response.status_code == 400:
            return False, "submitToIIR failed"
        if response.status_code >= 400:
            return False, f"submitToIIR error {response.status_code}"

        return True, ""

    except Exception as e:
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