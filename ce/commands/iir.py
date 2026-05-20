"""IIR command group: ce iir bulk-upload-dids sign-challenges / publish."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import click
from rich.console import Console

from ce.commands.iir_sign_challenge import sign_individual_challenge

from ce.auth.token_manager import require_login
from ce.config.context import require_environment
from ce.iir.csv_processor import run_generate, run_upload
from ce.iir.did_ops import extract_user_id_from_token
from ce.utils.errors import handle_api_errors

console = Console()
err_console = Console(stderr=True)


@click.group("iir")
def iir_group() -> None:
    """IIR (Issuer Identity Registry) commands."""


@iir_group.group("bulk-upload-dids")
def bulk_upload_dids_group() -> None:
    """Bulk DID challenge generation and issuer publishing."""

iir_group.add_command(sign_individual_challenge)

@bulk_upload_dids_group.command("sign-challenges")
@click.option(
    "--csv", "csv_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Input CSV file (columns: CTID, DID, VerificationMethod, Algorithm, PrivateKey, ValidFrom, ValidUntil).",
)
@click.option(
    "--output", "-o", "output_path",
    default=None,
    help="Output CSV path. Default: Output-<stem>-<UTC>.csv",
)
@click.option(
    "--errors", "errors_path",
    default=None,
    help="Errors CSV path. Default: Errors-<stem>-<UTC>.csv",
)
@handle_api_errors
def generate(csv_path: str, output_path: str | None, errors_path: str | None) -> None:
    """Check membership & registry, validate DIDs, create challenges, sign JWTs.

    \b
    Checks per row:
      1. CTID format
      2. Date format validation (ValidFrom, ValidUntil if provided)
      3. Membership check - Is User a member of the org
      4. Registry check - Is CTID published to the registry
      5. DID classification
      6. DID validation via API
      7. Verification method
      8. Create challenge
      9. Sign JWT
      10. Local JWT verification

    \b
    Input CSV columns (required):
      CTID, DID, VerificationMethod, Algorithm, PrivateKey

    \b
    Input CSV columns (optional):
      ValidFrom, ValidUntil  (format: MM/DD/YYYY)

    \b
    Produces two files:
      Output-<stem>-<UTC>.csv   — signed rows ready for publish
      Errors-<stem>-<UTC>.csv   — rows that failed, fix and rerun

    \b
    Examples:
      ce iir bulk-upload-dids sign-challenges --csv input.csv
      ce iir bulk-upload-dids sign-challenges --csv input.csv --output signed.csv
    """
    access_token = require_login()
    _, env = require_environment()

    try:
        user_id = extract_user_id_from_token(access_token)
    except ValueError as e:
        err_console.print(f"[red]✗[/red] {e}")
        raise SystemExit(1)

    stem      = Path(csv_path).stem
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    resolved_output = output_path or f"Output-{stem}-{timestamp}.csv"
    resolved_errors = errors_path or f"Errors-{stem}-{timestamp}.csv"

    console.print(f"\n[dim]Environment:[/dim] [bold]{env.label}[/bold]  ({env.publisher_base})")
    console.print(f"[dim]User ID:[/dim]      [bold]{user_id}[/bold]")

    ok, errors = run_generate(
        input_path=csv_path,
        output_path=resolved_output,
        errors_path=resolved_errors,
        access_token=access_token,
        env=env,
        user_id=user_id,
    )

    if ok > 0:
        console.print(
            f"\n[dim]Next step:[/dim] "
            f"[bold]ce iir bulk-upload-dids publish  --output-file \"{resolved_output}\"[/bold]"
        )



@bulk_upload_dids_group.command("publish")
@click.option(
    "--output-file", "output_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Output CSV produced by the sign-challenges step.",
)
@click.option(
    "--publish-errors", "publish_errors_path",
    default=None,
    help="Publish errors CSV path. Default: PublishErrors-<stem>-<UTC>.csv",
)
@click.option(
    "--yes", "-y",
    is_flag=True,
    default=False,
    help="Skip confirmation prompt.",
)
@handle_api_errors
def upload(output_path: str, publish_errors_path: str | None, yes: bool) -> None:
    """Verify JWT signatures and publish issuers.

    \b
    Steps per row:
      1. JWT signature verify  
      2. Save Token
      3. Submit to IIR        


    \b
    Examples:
      ce iir bulk-upload-dids publish --output-file Output-input-20240101T000000Z.csv
      ce iir bulk-upload-dids publish --output-file signed.csv --yes
    """
    access_token = require_login()
    _, env = require_environment()

    stem      = Path(output_path).stem
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    resolved_pub_errors = publish_errors_path or f"PublishErrors-{stem}-{timestamp}.csv"

    console.print(f"\n[dim]Environment:[/dim] [bold]{env.label}[/bold]  ({env.publisher_base})")

    run_upload(
        output_path=output_path,
        publish_errors_path=resolved_pub_errors,
        access_token=access_token,
        env=env,
        yes=yes,
    )