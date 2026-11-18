# Regenerates the Publisher client. Run from any folder: the script moves to its own.
#
#   1. Save the Publisher's Swagger document next to this script (the Publisher must be running):
#        Invoke-WebRequest http://localhost:8011/swagger/v1/swagger.json -OutFile swagger.json
#   2. .\generate-client.ps1
#
# prepare_openapi.py keeps application/json where the Publisher also offers text/plain, so answers are read as JSON.
# Generate with openapi-python-client 0.30 or newer: it writes the httpx2 code ce-cli uses.
# Ruff must be on PATH (pip install ruff): the generator runs it to drop unused imports and format the files. Without it
# the output keeps hundreds of unused imports, which the code-quality check flags.
Set-Location $PSScriptRoot

if (-not (Test-Path swagger.json)) {
    Write-Error "swagger.json not found in $PSScriptRoot"
    exit 1
}
if (-not (Get-Command ruff -ErrorAction SilentlyContinue)) {
    Write-Error "ruff not found in PATH. Run: pip install ruff"
    exit 1
}

python prepare_openapi.py swagger.json openapi.json
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m openapi_python_client generate `
    --path openapi.json `
    --config openapi-client-config.yml `
    --output-path generated-client `
    --overwrite
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Publisher SDK regenerated in $PSScriptRoot\generated-client"
