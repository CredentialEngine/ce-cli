pip install openapi-python-client --user

python -m openapi_python_client generate `
    --path ce/iir/openapi.json `
    --config ce/iir/api/openapi-client-config.yml `
    --output-path ce/iir/api `
    --overwrite

Write-Host "`n--- OUTPUT ---"
Get-Content generate.log