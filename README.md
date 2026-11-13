# Credential Engine CLI (`ce`)

A command-line tool for managing Credential Engine platform resources.

## Requirements
 
- Python 3.10 or later
- `pip`
## Installation
 
> **Recommended:** install inside a virtual environment. This avoids file-permission errors, PATH conflicts, and "invalid distribution" warnings from previous installs.
 
### Option 1: Install from source with a virtual environment (recommended)
 
**macOS / Linux:**
 
```bash
git clone https://github.com/CredentialEngine/ce-cli.git
cd ce-cli
 
python3 -m venv .venv
source .venv/bin/activate
 
pip install -e .
```
 
**Windows (PowerShell):**
 
```powershell
git clone https://github.com/CredentialEngine/ce-cli.git
cd ce-cli
 
python -m venv .venv
.venv\Scripts\activate
 
pip install -e .
```
 
When the venv is active you'll see `(.venv)` in your prompt, and `ce` is automatically on `PATH`. To leave the venv, run `deactivate`. To re-enter it next time, run the activate command above from the project folder.
 
### Option 2: Install from a release
 
1. Download the `.whl` from the [Releases page](https://github.com/CredentialEngine/ce-cli/releases).
2. Install it (inside a venv is still recommended):
   ```bash
   pip install ce_cli-<version>-py3-none-any.whl
   ```

 ### Upgrading
 
From a release `.whl`:
 
```bash
pip install --upgrade ce_cli-<version>-py3-none-any.whl
```
 
From source: `git pull` and re-run `pip install -e .` inside your venv.
 
### Option 3: Install from source without a venv
 
```bash
git clone https://github.com/CredentialEngine/ce-cli.git
cd ce-cli
pip install -e .
```
 
This puts the `ce` command on your `$PATH`. On Windows, see the [Windows PATH note](#windows-path-note) below if `ce` isn't found.
 
### Verify the installation
 
```bash
ce --help
```
 
You should see the top-level command list.
 
### Windows PATH note
 
When you install on Windows without a venv, pip often drops ce.exe into your user Scripts folder, which Windows doesn't put on PATH by default:
 
```
C:\Users\<you>\AppData\Roaming\Python\Python310\Scripts
```
 
If `ce --help` fails after install, either use a venv (recommended) or add that folder to your User PATH:
 
```powershell
[Environment]::SetEnvironmentVariable(
  "Path",
  $env:Path + ";C:\Users\$env:USERNAME\AppData\Roaming\Python\Python310\Scripts",
  "User"
)
```
 
Then **close and reopen PowerShell** existing windows won't pick up the new PATH.
 


## Quick start

```bash
# Pick an environment, then sign in
ce env list
ce env use dev
ce login
ce whoami
```

## Command reference

### Account (`ce`)

| Command     | Description                               |
| ----------- | ----------------------------------------- |
| `ce login`  | Sign in via Keycloak device authorization |
| `ce logout` | Sign out and revoke tokens                |
| `ce whoami` | Show who you're signed in as              |

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

### Publisher — API publishing (`ce publisher`)

Publish to the Credential Registry through a **project**: create it, add files, validate them, fix what validation
finds, then complete it. The Publisher has three kinds of project; ce-cli works with two:

- **Bulk upload (BU)**, the default and the standard project: **BU template CSVs**. The columns are the ones of the
  Publisher's BU templates, for example the Credentials template. One class of file per `add`. A CSV you upload with
  ce-cli is a BU project, the same project the Publisher UI makes.
- **API publishing**, created with `--jsonld`: **JSON-LD only**, in the shape the CSV transform produces, an array of
  graphs, each with `@context`, `@id` and `@graph`. CSVs are refused.
- **Ruby Registry sync** is made by the Ruby Registry when it uploads a changeset. `ce publisher project list` shows
  it; ce-cli adds no files to it, validates it or completes it.

| Command | Description |
| ------- | ----------- |
| `ce publisher project create --name <name> [--jsonld]` | Create a project. A BU project is the default; `--jsonld` makes an API publishing project |
| `ce publisher project add --project-id <id> --file <file or folder> [--type <template>]` | Add files, or replace the files of the same name. A BU project needs `--type`, the BU template the files follow: `credentials`, `learning-opportunities`, `assessments`, `jobs`, … Repeat `--file` for several; `--recursive` for subfolders |
| `ce publisher project run validation --project-id <id>` | Validate the latest iteration, including the CTIDs it refers to. A BU project starts validating when files are added, so this waits for it (`--no-wait` to return at once) |
| `ce publisher project show validation status --project-id <id>` | How many files passed and how many have errors (`--verbose` lists each one) |
| `ce publisher project show validation errors --project-id <id>` | The errors to fix |
| `ce publisher project show status --project-id <id>` | The project, its latest iteration and each publishing stage |
| `ce publisher project show audit --project-id <id>` | Who did what, oldest first |
| `ce publisher project complete --project-id <id>` | Approve the project and publish it (`--no-wait` to return at once). Run again to retry a failed publish |
| `ce publisher project list` | Your projects |
| `ce publisher project abandon --project-id <id>` | Abandon a project that was not published |

Every `show` command takes `-o json`.

```text
ce publisher project create --name "Welding certificates"
ce publisher project add --project-id 23 --file credentials.csv --type credentials
ce publisher project run validation --project-id 23
ce publisher project show validation errors --project-id 23
ce publisher project add --project-id 23 --file fixed\credentials.csv --type credentials
ce publisher project run validation --project-id 23
ce publisher project complete --project-id 23
ce publisher project show audit --project-id 23
```

How it behaves:

- **Adding** a CSV to a BU project starts validation at once. Adding a JSON-LD file to an API publishing project only stores it; run validation when you have
  added everything.
- **Validation** checks the files and also looks up every CTID they refer to, with the same rules as the bulk
  upload.
- **A change after validation** starts a new iteration, which begins as a copy of the last one. A file with the same
  name replaces the earlier one.
- **Completing** needs a latest iteration that validated without errors. For a BU project it first transforms the
  CSV files to JSON-LD and makes you a reviewer, so you can approve; then it approves and publishes. Each step is
  recorded in the audit log.
- **Only you** can change an API publishing project you created.
- **Exit status** is 1 when a file was refused, validation found errors, or the project did not publish.

The Publisher API address comes from the environment (`publisher_api_base`); override it with `--publisher-url` or
`CE_PUBLISHER_API_URL`. Your account needs the Publisher user role and a tenant on its profile.

The commands call the Publisher through a client generated from its Swagger document
(`ce/publisher/api/publisher_client`). `generate.ps1` regenerates it. The legacy Registry Assistant request format is
a Publisher feature flag that is off by default; ce-cli does not offer it, and a client generated while it is off has
no call for it.

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
    │   ├── auth.py                # ce login / logout / whoami
    │   ├── env.py                 # ce env list / use / show / add / remove
    │   ├── config.py              # ce config set / get / list / reset
    │   ├── iir.py                 # ce iir challenge bulk-sign, ce iir issuer-did publish
    │   ├── iir_sign_challenge.py  # ce iir challenge sign
    │   ├── publisher.py           # ce publisher project ... / format
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
