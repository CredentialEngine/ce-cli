# Credential Engine CLI (`ce`)

A command-line tool for managing Credential Engine platform resources.

All commands follow the format:

```
ce <noun> [<noun>] <verb> [--<parameters>]
```

## Requirements

- Python 3.10+

## Installation

```bash
pip install -e .
```

This puts the `ce` command on your `$PATH`.

## Quick start

```bash
# Pick an environment, then sign in
ce env list
ce env use dev
ce account login
ce account show
```

## Command reference

### Account (`ce account`)

| Command             | Description                               |
| ------------------- | ----------------------------------------- |
| `ce account login`  | Sign in via Keycloak device authorization |
| `ce account logout` | Sign out and revoke tokens                |
| `ce account show`   | Show who you're signed in as              |

### Environments (`ce env`)

Environments let you switch between `dev`, `sandbox`, and `prod` without touching env vars. Each environment maps a friendly name to an API URL (plus optional OIDC overrides).

| Command             | Description                                    |
| ------------------- | ---------------------------------------------- |
| `ce env list`       | List all environments (● marks the active one) |
| `ce env use <name>` | Switch to a different environment              |

```bash
ce env list
ce env use dev
```

### IIR — Issuer Identity Registry (`ce iir`)

IIR commands are grouped by the noun they operate on:

- `ce iir challenge ...` — sign challenges (single or bulk)
- `ce iir issuer-did ...` — publish signed issuers to the registry

| Command                      | Login required | Description                                                  |
| ---------------------------- | -------------- | ------------------------------------------------------------ |
| `ce iir challenge sign`      | No             | Sign a single CE challenge JSON file and produce a Proof JWT |
| `ce iir challenge bulk-sign` | Yes            | Bulk-validate and sign challenges from a CSV                 |
| `ce iir issuer-did publish`  | Yes            | Publish signed issuers to the IIR registry                   |

#### Sign a single challenge (`ce iir challenge sign`)

Signs a CE-generated challenge JSON file with an Ed25519 private key (alg `EdDSA`) and verifies the resulting JWT against the public key resolved from the DID in the payload. No login required — offline for `did:key`, single HTTPS fetch for `did:web`.

```bash
ce iir challenge sign \
  --private-key z3u2en... \
  --challenge-file challenge.json \
  --output signed-challenge.jwt
```

| Flag               | Required | Description                                                          |
| ------------------ | -------- | -------------------------------------------------------------------- |
| `--private-key`    | Yes      | Ed25519 private seed, multibase base58btc (starts with `z`)          |
| `--challenge-file` | Yes      | Path to the challenge JSON produced by CE                            |
| `--output`, `-o`   | No       | Write the JWT to this file. If omitted, the JWT is printed to stdout |

The challenge JSON must include `did`, `challenge`, `aud`, `iat`, and `exp`. The `did` field is used as the JWT header `kid` and to resolve the public key for verification (`did:key` resolves offline; `did:web` is fetched over HTTPS using the OS trust store).

Example challenge file:

```json
{
  "did": "did:key:z6Mkh...#z6Mkh...",
  "challenge": "abc123-nonce",
  "aud": "https://credentialengine.org/iir",
  "iat": 1779317055,
  "exp": 1779317655
}
```

On success, the JWT is written (or printed) and a verification confirmation is shown on stderr:

```
Signature verification: OK (matches DID public key)
Wrote Proof JWT to: signed-challenge.jwt
```

#### Bulk DID upload

Register DIDs for multiple organizations in one go. The process has two phases.

**Phase 1 — Sign challenges (`ce iir challenge bulk-sign`):**

```bash
ce iir challenge bulk-sign --csv input.csv --output output.csv
```

Validates each row (membership, registry lookup, DID resolution), creates challenges, signs JWTs with the provided private keys, and writes the results to an output CSV. If `--output` is omitted, defaults to `Output-<stem>-<UTC>.csv`. Failed rows are written to `Errors-<stem>-<UTC>.csv` (override with `--errors`).

**Phase 2 — Publish to the IIR registry (`ce iir issuer-did publish`):**

```bash
ce iir issuer-did publish --input output.csv
```

Verifies the JWT signatures and publishes each issuer to the IIR. Pass `--yes`/`-y` to skip the confirmation prompt. Failed publishes are written to `PublishErrors-<stem>-<UTC>.csv` (override with `--publish-errors`).

#### Input CSV format

| Column               | Required    | Description                                                   |
| -------------------- | ----------- | ------------------------------------------------------------- |
| `CTID`               | Yes         | The organization's CTID (must be published in the registry)   |
| `DID`                | Yes         | `did:key:...` or `did:web:...`                                |
| `VerificationMethod` | Yes         | Full verification method ID (e.g., `did:key:z6Mk...#z6Mk...`) |
| `Algorithm`          | For did:key | `Ed25519`, `secp256k1`, `P-256`, or `X25519`                  |
| `PrivateKey`         | Yes         | Multibase-encoded private key for signing                     |
| `ValidFrom`          | No          | Date when the issuer becomes valid (MM/DD/YYYY)               |
| `ValidUntil`         | No          | Date when the issuer expires (MM/DD/YYYY)                     |

Example:

```csv
CTID,DID,VerificationMethod,Algorithm,PrivateKey,ValidFrom,ValidUntil
ce-12345678-...,did:key:z6MkhaX...,did:key:z6MkhaX...#z6MkhaX...,Ed25519,z3u2en...,01/01/2024,12/31/2025
ce-87654321-...,did:web:example.com,did:web:example.com#key-1,,z3u2en...,,
```

`ValidFrom` and `ValidUntil` are optional.

## Project structure

```
ce-cli/
├── pyproject.toml
└── ce/
    ├── main.py                    # Root CLI group
    ├── auth/
    │   ├── device_flow.py         # RFC 8628 Keycloak client
    │   └── token_manager.py       # Silent token refresh + require_login()
    ├── commands/
    │   ├── auth.py                # ce account login / logout / show
    │   ├── env.py                 # ce env list / use / show / add / remove
    │   ├── config.py              # ce config set / get / list / reset
    │   ├── iir.py                 # ce iir challenge bulk-sign, ce iir issuer-did publish
    │   ├── iir_sign_challenge.py  # ce iir challenge sign
    │   └── resource.py            # ce resource list / show / create / delete
    ├── config/
    │   ├── settings.py            # OIDCSettings, token I/O, paths
    │   └── context.py             # Environment model, active-env helpers
    ├── iir/
    │   ├── csv_processor.py       # Bulk DID upload (bulk-sign + publish)
    │   └── did_ops.py             # DID validation, challenges, JWT signing
    └── utils/
        ├── http.py                # Authenticated httpx wrapper + APIError
        ├── output.py              # table/json/yaml/tsv renderer + @output_option
        └── errors.py              # @handle_api_errors decorator
```
