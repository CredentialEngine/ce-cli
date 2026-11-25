# Publisher API Python SDK

- `swagger.json`: the Publisher API's Swagger document.
- `prepare_openapi.py`: makes `swagger.json` readable for the generator (keeps `application/json`); writes `openapi.json`.
- `openapi.json`: the prepared document the generator reads. Do not edit.
- `openapi-client-config.yml`: names the generated package `publisher_client`.
- `generate-client.ps1`: regenerates the SDK on Windows.
- `generated-client/publisher_client`: generated Python code; do not hand edit.

To regenerate, save a fresh `swagger.json` from the Publisher host, then run `generate-client.ps1` from PowerShell. It needs
`pip install openapi-python-client==0.30.0 ruff` (0.30 writes the httpx2 code ce-cli uses).

## Installing

The root `pyproject.toml` packages `publisher_client` alongside `ce` into the **same Python distribution**, the way ceops packages
its Consumer API SDK. From the repository root:

```powershell
python -m pip install -e ".[dev]"
python -c "import publisher_client; print(publisher_client.__file__)"
```

Do not install `generated-client` separately. Changing `swagger.json` alone changes nothing: regenerate, then reinstall.

`ce/implementations/publisher/client.py` is the only code that imports the SDK.
