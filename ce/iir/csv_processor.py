"""CSV processing for bulk DID upload.
  sign-challenges
        CTID Validation  
        registry lookup,
        DID validation,
        challenge creation, 
        JWT signing  
            Output CSV
  publish
        JWT signature verify
        Save Token
        publish issuer
"""

from __future__ import annotations

import csv
from pathlib import Path

from rich.console import Console
from rich.table import Table, box

from ce.iir.did_ops import (
    call_get_organization_iir_detail,
    call_is_user_member,
    call_create_challenges,
    call_get_registry_resource,
    call_save_challenge_token, 
    call_validate_did_key,
    call_validate_did_web,
    call_verify_jwt_signature,
    classify_did,
    merge_autofill,
    sign_proof_jwt,
    validate_ctid,
    validate_date,
    validate_did_key_prefix,
    validate_verification_method,
    verify_proof_jwt,
    call_submit_to_iir
)

console = Console()
err_console = Console(stderr=True)


OUTPUT_FIELDS      = ["CTID", "DID", "VerificationMethod", "Challenge", "ProofJWT", "ValidFrom", "ValidUntil"]
ERROR_FIELDS       = ["CTID", "DID", "VerificationMethod", "Algorithm", "Error"]
PUBLISH_ERR_FIELDS = ["CTID", "DID", "VerificationMethod", "Challenge", "Error"]


def run_generate(
    input_path: str,
    output_path: str,
    errors_path: str,
    access_token: str,
    env,        
    user_id: str,
) -> tuple[int, int]:
    """Validate membership, registry, DIDs, create challenges, sign JWTs.

    Steps per row:
      1. Validate CTID format
      2. Membership check       — is the user a member of this org?
      3. Registry check         — is the CTID published in the registry?
      4. Classify DID + prefix check
      5. DID API validation
      6. Validate verification method
      7. Create challenge
      8. Sign JWT
      9. Local JWT verification

    Returns (ok_count, error_count).
    """
    input_file  = Path(input_path)
    output_file = Path(output_path)
    errors_file = Path(errors_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with input_file.open(newline="", encoding="utf-8-sig") as f:
        reader   = csv.DictReader(f)
        norm_map = {field: field.strip().lower() for field in (reader.fieldnames or [])}
        rows = [{norm_map[k]: (v.strip() if v is not None else "") for k, v in row.items()} for row in reader ]

    missing = [c for c in ("ctid", "did", "verificationmethod") if c not in norm_map.values()]
    if missing:
        raise ValueError(f"Missing required CSV column(s): {', '.join(missing)}")

    ok_rows    : list[dict] = []
    error_rows : list[dict] = []
    total = len(rows)

    table = Table(box=box.SIMPLE_HEAD, header_style="bold", border_style="dim", show_lines=False)
    table.add_column("#",        width=4,  style="dim")
    table.add_column("CTID",     width=44)
    table.add_column("Member",   width=8)
    table.add_column("Registry", width=10)
    table.add_column("DID type", width=10)
    table.add_column("Result",   width=36)

    console.print(f"\n[bold]Processing {total} row(s) from '{input_path}'…[/bold]\n")

    for i, row in enumerate(rows, 1):
        ctid    = row.get("ctid", "")
        did     = row.get("did", "")
        vm      = row.get("verificationmethod", "")
        alg     = row.get("algorithm", "")
        privkey = row.get("privatekey", "")
        valid_from  = row.get("validfrom", "")
        valid_until = row.get("validuntil", "")
        did_type      = "unknown"
        error         = ""
        member_icon   = "[dim]—[/dim]"
        registry_icon = "[dim]—[/dim]"
        registry_data : dict = {}

        def fail(reason: str) -> None:
            nonlocal error
            error = reason

        ctid_ok, ctid_err = validate_ctid(ctid)
        if not ctid_ok:
            fail(ctid_err)
        
        if not error:
            ok, err, valid_from = validate_date(valid_from, "ValidFrom")
            if not ok:
                fail(err)
        if not error:
            ok, err, valid_until = validate_date(valid_until, "ValidUntil")
            if not ok:
                fail(err)

        if not error:
            ok, err = call_is_user_member(
                user_id, ctid, access_token, env.publisher_base, env.ssl_verify
            )
            member_icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
            if not ok:
                fail(err)

        if not error:
            ok, registry_data, err = call_get_registry_resource(
                ctid, access_token, env.publisher_base, env.ssl_verify
            )
            registry_icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
            if not ok:
                fail(err)

        if not error:
            did_type, type_err = classify_did(did)
            if type_err:
                fail(type_err)
            elif did_type == "did:key":
                ok, err = validate_did_key_prefix(did, alg)
                if not ok:
                    fail(err)

        api_vm_ids: list[str] = []
        if not error:
            if did_type == "did:key":
                ok, data, err = call_validate_did_key(did, alg, access_token, env.publisher_base, env.ssl_verify)
            else:
                ok, data, err = call_validate_did_web(did, access_token, env.publisher_base, env.ssl_verify)
            if not ok:
                fail(err)
            else:
                api_vm_ids = data.get("VerificationMethodIds") or data.get("verificationMethodIds") or []

        if not error:
            ok, err = validate_verification_method(vm, did, api_vm_ids)
            if not ok:
                fail(err)

        challenge_uuid    = ""
        challenge_payload = {}
        if not error:
            ok, challenges_list, err = call_create_challenges(
                ctid, [vm], access_token, env.publisher_base, env.ssl_verify
            )
            if not ok:
                fail(err)
            elif not challenges_list:
                fail("createChallenges returned no challenges")
            else:
                challenge = next(
                    (c for c in challenges_list if (c.get("Did") or c.get("did")) == vm),
                    challenges_list[0],
                )
                challenge_uuid = challenge.get("Challenge") or challenge.get("challenge", "")
                challenge_payload = {
                    "did":       challenge.get("Did")       or challenge.get("did", did),
                    "challenge": challenge_uuid,
                    "aud":       challenge.get("Aud")       or challenge.get("aud", ""),
                    "iat":       challenge.get("Iat")       or challenge.get("iat", 0),
                    "exp":       challenge.get("Exp")       or challenge.get("exp", 0),
                    "ctid":      ctid,
                }

        proof_jwt = ""
        if not error:
            if not privkey:
                fail("PrivateKey is required for JWT signing")
            else:
                try:
                    proof_jwt = sign_proof_jwt(privkey, vm, challenge_payload)
                except Exception as e:
                    fail(f"JWT signing failed: {e}")

        if not error:
            ok, err = verify_proof_jwt(proof_jwt, vm)
            if not ok:
                fail(err)

        ctid_short = (ctid[:42] + "…") if len(ctid) > 43 else ctid

        if not error:
            result = f"[green]✓[/green] {challenge_uuid[:20]}…"
            ok_rows.append({
                "CTID":               ctid,
                "DID":                did,
                "VerificationMethod": vm,
                "Challenge":          challenge_uuid,
                "ProofJWT":           proof_jwt,
                "ValidFrom":          valid_from,
                "ValidUntil":         valid_until,
            })
        else:
            result = f"[red]✗[/red] {error[:36]}"
            error_rows.append({
                "CTID":               ctid,
                "DID":                did,
                "VerificationMethod": vm,
                "Algorithm":          alg,
                "Error":              error,
            })

        table.add_row(str(i), ctid_short, member_icon, registry_icon, did_type, result)

    console.print(table)

    with output_file.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(ok_rows)

    with errors_file.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ERROR_FIELDS)
        writer.writeheader()
        writer.writerows(error_rows)

    console.print(f"\n[green]✓[/green] {len(ok_rows)} succeeded  →  [bold]{output_file}[/bold]")
    if error_rows:
        console.print(f"[red]✗[/red] {len(error_rows)} failed     →  [bold]{errors_file}[/bold]")
        console.print(
            f"  Fix errors and rerun: "
            f"[bold]ce iir bulk-upload-dids sign-challenges --csv {errors_file.name}[/bold]"
        )

    return len(ok_rows), len(error_rows)


def run_upload(
    output_path: str,
    publish_errors_path: str,
    access_token: str,
    env,
    yes: bool = False,
) -> None:
    
    output_file      = Path(output_path)
    publish_err_file = Path(publish_errors_path)

    if not output_file.exists() or output_file.stat().st_size == 0:
        console.print("\nOutput file is empty or missing — nothing to upload.")
        return

    with output_file.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        console.print("Output CSV has no rows.")
        return

    if not yes:
        import click
        click.confirm(f"\n  Publish {len(rows)} issuer(s) from '{output_path}'?", abort=True)

    publish_error_rows: list[dict] = []

    table = Table(box=box.SIMPLE_HEAD, header_style="bold", border_style="dim")
    table.add_column("#",       width=4,  style="dim")
    table.add_column("CTID",    width=44)
    table.add_column("JWT",     width=6)
    table.add_column("Publish", width=9)

    console.print(f"\n[bold]Publishing {len(rows)} issuer(s)…[/bold]\n")

    for i, row in enumerate(rows, 1):
        ctid           = row["CTID"]
        did            = row["DID"]
        proof_jwt      = row["ProofJWT"]
        challenge_uuid = row["Challenge"]
        vm             = row["VerificationMethod"]
        valid_from     = row.get("ValidFrom", "")
        valid_until    = row.get("ValidUntil", "")
        ctid_short     = (ctid[:42] + "…") if len(ctid) > 43 else ctid
        pub_error      = ""
        jwt_icon       = "[dim]—[/dim]"
        publish_icon   = "[dim]—[/dim]"

        def pub_fail(reason: str) -> None:
            nonlocal pub_error
            pub_error = reason

        ok, err = call_verify_jwt_signature(
            proof_jwt, challenge_uuid, access_token, env.publisher_base, env.ssl_verify
        )
        jwt_icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
        if not ok:
            pub_fail(err)

        if not pub_error:
            ok, err = call_save_challenge_token(
                ctid, challenge_uuid, proof_jwt,
                access_token, env.publisher_base, env.ssl_verify,
            )
            if not ok:
                pub_fail(err)

        if not pub_error:
            ok, registry_data, err = call_get_registry_resource(
                ctid, access_token, env.publisher_base, env.ssl_verify
            )
            if not ok:
                pub_fail(err)
            else:
                ok_acc, accounts_data, acc_err = call_get_organization_iir_detail(
                    ctid, access_token, env.publisher_base, env.ssl_verify
                )
                if not ok_acc:
                    accounts_data = {}

                merged = merge_autofill(registry_data, accounts_data)
                ok, err = call_submit_to_iir(
                    ctid, did,
                    merged["name"],
                    merged["legal_name"],
                    merged["registry_uri"],
                    merged["subject_webpage"],
                    access_token, env.publisher_base, env.ssl_verify,
                    logo_uri=merged["image"],
                    logo_base64=merged["logo_base64"],
                    valid_from=valid_from,
                    valid_until=valid_until,
                )
                publish_icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
                if not ok:
                    pub_fail(err)

        if pub_error:
            publish_error_rows.append({
                "CTID": ctid, "DID": did,
                "VerificationMethod": vm, "Challenge": challenge_uuid,
                "Error": pub_error,
            })

        table.add_row(str(i), ctid_short, jwt_icon, publish_icon)

    console.print(table)

    with publish_err_file.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PUBLISH_ERR_FIELDS)
        writer.writeheader()
        writer.writerows(publish_error_rows)

    ok_count = len(rows) - len(publish_error_rows)
    console.print(f"\n[green]✓[/green] {ok_count} published successfully.")
    if publish_error_rows:
        console.print(
            f"[red]✗[/red] {len(publish_error_rows)} error(s)  →  [bold]{publish_err_file}[/bold]"
        )