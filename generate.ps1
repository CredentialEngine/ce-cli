npm install -g swagger2openapi
pip install openapi-python-client --user

swagger2openapi ce/iir/swagger.json -o ce/iir/openapi.json

python -m openapi_python_client generate `
    --path ce/iir/openapi.json `
    --config ce/iir/api/openapi-client-config.yml `
    --output-path ce/iir/api `
    --overwrite

Write-Host "`n--- OUTPUT ---"
Get-Content generate.log