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
# Publisher client (ce publisher). Save the Publisher's Swagger document as ce/publisher/swagger.json first:
#   Invoke-WebRequest http://localhost:8011/swagger/v1/swagger.json -OutFile ce/publisher/swagger.json
# prepare_openapi.py keeps application/json where the Publisher also offers text/plain, so answers are read as JSON.
# Generate with openapi-python-client 0.26 or older: later versions write code for httpx2, which ce-cli does not use.
python ce/publisher/prepare_openapi.py ce/publisher/swagger.json ce/publisher/openapi.json

python -m openapi_python_client generate `
    --path ce/publisher/openapi.json `
    --config ce/publisher/api/openapi-client-config.yml `
    --output-path ce/publisher/api `
    --overwrite
