# Credential Engine CLI (`ce`)

A command-line tool for managing Credential Engine platform resources. 



## Requirements

- Python 3.10+



## Installation

```bash
pip install -e .
```

This puts the `ce` command on your `$PATH`.


## Quick start

```bash
# Sign in
ce login

```


## Command reference

### Authentication

| Command | Description |
|---|---|
| `ce login` | Sign in via Keycloak device authorization |
| `ce logout` | Sign out and revoke tokens |
| `ce whoami` | Show who you're signed in as |

### Environments (`ce env`)

Environments let you switch between `dev`, `sandbox`, and `prod` without touching env vars. Each environment maps a friendly name to an API URL (plus optional OIDC overrides).

| Command | Description |
|---|---|
| `ce env list` | List all environments (● marks the active one) |
| `ce env use <n>` | Switch to a different environment |

```bash
ce env list
ce env use dev
```


### Bulk DID Upload (`ce iir bulk-upload-dids`)

Register DIDs for multiple organizations in one go. The process has two phases:

**Phase 1 — Generate signed challenges:**

```bash
ce iir bulk-upload-dids sign-challenges --csv input.csv
```

Validates each row (membership, registry lookup, DID resolution), creates challenges, signs JWTs with the provided private keys, and writes the results to an output CSV.

**Phase 2 — Publish to the IIR registry:**

```bash
ce iir bulk-upload-dids publish --output-file Output-input-20240101T000000Z.csv
```

Verifies the JWT signatures server-side and publishes each issuer to the IIR.

#### Input CSV format

| Column | Required | Description |
|---|---|---|
| `CTID` | Yes | The organization's CTID (must be published in the registry) |
| `DID` | Yes | `did:key:...` or `did:web:...` |
| `VerificationMethod` | Yes | Full verification method ID (e.g., `did:key:z6Mk...#z6Mk...`) |
| `Algorithm` | For did:key | `Ed25519`, `secp256k1`, `P-256`, or `X25519` |
| `PrivateKey` | Yes | Multibase-encoded private key for signing |
| `ValidFrom` | No | Date when the issuer becomes valid (MM/DD/YYYY) |
| `ValidUntil` | No | Date when the issuer expires (MM/DD/YYYY) |

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
    ├── main.py                  # Root CLI group + top-level aliases
    ├── auth/
    │   ├── device_flow.py       # RFC 8628 Keycloak client
    │   └── token_manager.py     # Silent token refresh + require_login()
    ├── commands/
    │   ├── auth.py              # ce login / logout / account show
    │   ├── env.py               # ce env list/add/use/show/remove
    │   ├── config.py            # ce config set/get/list/reset
    │   └── resource.py          # ce resource list/show/create/delete
    ├── config/
    │   ├── settings.py          # OIDCSettings, token I/O, paths
    │   └── context.py           # Environment model, active-env helpers
    ├── iir/
    │   ├── csv_processor.py     # Bulk DID upload (sign-challenges + publish)
    │   └── did_ops.py           # DID validation, challenges, JWT signing
    └── utils/
        ├── http.py              # Authenticated httpx wrapper + APIError
        ├── output.py            # table/json/yaml/tsv renderer + @output_option
        └── errors.py            # @handle_api_errors decorator
```
