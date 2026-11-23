"""ce iir challenge sign

  ce iir challenge sign --algorithm Ed25519 --private-key zABC... \
    --challenge-file challenge.json --output signed-challenge.jwt

  ce iir challenge sign --algorithm RS256 --private-key rsa-key.pem \
    --challenge-file challenge.json --output signed-challenge.jwt

Signs one CE challenge and produces a Proof JWT, then verifies it against the
public key resolved from the DID (did:key or did:web). No login required.
--algorithm picks the implementation:

  Ed25519  alg=EdDSA, --private-key is a multibase seed (z...).
           ce.implementations.iir_challenge_sign_ed25519
  RS256    alg=RS256, --private-key is a PEM file path or the PEM text.
           ce.implementations.iir_challenge_sign_rs256
"""

from __future__ import annotations

import json
from typing import Any, Dict

import click
from rich.console import Console

from ce.implementations import iir_challenge_sign_ed25519 as _ed25519
from ce.implementations import iir_challenge_sign_rs256 as _rs256

err_console = Console(stderr=True)

ALGORITHM_ED25519 = "Ed25519"
ALGORITHM_RS256 = "RS256"

REQUIRED_FIELDS = ["did", "challenge", "aud", "iat", "exp"]



# Input checks

def read_challenge(challenge_file: str) -> Dict[str, Any]:
    """Load the challenge JSON and check it has the fields a Proof JWT needs."""
    try:
        with open(challenge_file, "r", encoding="utf-8") as f:
            payload_obj = json.load(f)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Challenge file is not valid JSON: {e}")

    if not isinstance(payload_obj, dict):
        raise click.ClickException("Challenge payload must be a JSON object.")

    missing = [k for k in REQUIRED_FIELDS if k not in payload_obj]
    if missing:
        raise click.ClickException(
            f"Challenge JSON missing required field(s): {', '.join(missing)}"
        )

    did_value = payload_obj.get("did")
    if not isinstance(did_value, str) or not did_value.strip():
        raise click.ClickException(
            'Challenge JSON must include a non-empty string field "did".'
        )

    return payload_obj


def looks_like_rsa_key(value: str) -> bool:
    """True when an Ed25519 --private-key value looks like a PEM key or a key file path."""
    if "-----BEGIN" in value or "\\n" in value:
        return True
    return _rs256.is_existing_file(value)



# Click command

@click.command(name="sign")
@click.option(
    "--algorithm",
    "algorithm",
    required=True,
    type=click.Choice([ALGORITHM_ED25519, ALGORITHM_RS256]),
    help="Signing algorithm: Ed25519 (alg=EdDSA) or RS256 (RSA).",
)
@click.option(
    "--private-key",
    "private_key",
    required=True,
    metavar="KEY",
    help=(
        "Ed25519: private seed (multibase base58btc, starts with 'z'). "
        "RS256: path to an unencrypted PEM/DER key file, or the PEM text."
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
def main(
    algorithm: str,
    private_key: str,
    challenge_file: str,
    out_path: str | None,
) -> None:
    """Sign a single CE challenge JSON file and produce a Proof JWT.

    \b
    --algorithm Ed25519 : --private-key is the multibase seed (z...).
    --algorithm RS256   : --private-key is a PEM file path or the PEM text.
    The challenge JSON must include: did, challenge, aud, iat, exp.
    Signature verification uses did:key (offline) or did:web (HTTPS).

    \b
    Examples:
      ce iir challenge sign --algorithm Ed25519 \\
        --private-key zABC... \\
        --challenge-file challenge.json \\
        --output signed-challenge.jwt

    \b
      ce iir challenge sign --algorithm RS256 \\
        --private-key rsa-key.pem \\
        --challenge-file challenge.json \\
        --output signed-challenge.jwt
    """
    payload_obj = read_challenge(challenge_file)
    kid = payload_obj["did"].strip()

    if algorithm == ALGORITHM_RS256:
        token = _rs256.sign_and_verify(private_key, kid, payload_obj)
    else:
        if looks_like_rsa_key(private_key):
            raise click.ClickException(
                "This looks like an RSA/PEM key. Use --algorithm RS256 for RSA keys."
            )
        token = _ed25519.sign_and_verify(private_key, kid, payload_obj)

    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(token)
        err_console.print(f"Wrote Proof JWT to: [cyan]{out_path}[/cyan]")
    else:
        click.echo(token)


if __name__ == "__main__":
    main()
