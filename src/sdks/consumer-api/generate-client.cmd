@echo off
setlocal
cd /d "%~dp0"

if not exist "swagger.json" (
    echo ERROR: swagger.json not found in %CD%
    exit /b 1
)

if not exist "node_modules\.bin\openapi-generator-cli.cmd" (
    echo ERROR: Local OpenAPI Generator CLI not found.
    echo Run npm ci in %CD% and retry.
    exit /b 1
)

call "node_modules\.bin\openapi-generator-cli.cmd" generate ^
  -i "swagger.json" ^
  -g python ^
  -o "./generated-client" ^
  --additional-properties=packageName=consumer_api_client,library=httpx2 ^
  --name-mappings "$type=discriminator_type"

if errorlevel 1 exit /b 1
echo Consumer API SDK regenerated in %CD%\generated-client
endlocal
