# Consumer API Python SDK

- `swagger.json`: Consumer API OpenAPI document.
- `generate-client.cmd`: regenerate the SDK on Windows using the installed `openapi-generator-cli`.
- `generated-client/consumer_api_client`: generated Python code; do not hand edit.

To regenerate, refresh `swagger.json` from the desired Consumer API host, then run `generate-client.cmd` from Command Prompt. The script uses `library=httpx` and maps JSON `$type` to the Python identifier `discriminator_type`; verify the generated JSON alias when upgrading the generator.

## Installing

The root `ceops/pyproject.toml` packages `consumer_api_client` alongside `ceops` into the **same Python distribution**. From the repository root, run:

```powershell
python -m pip install -e ".[dev]"
python -c "import consumer_api_client; print(consumer_api_client.__file__)"
```

The existing Dockerfile uses `pip install .`, which also installs the generated SDK automatically. Do not run `pip install -e ./src/sdks/consumer-api/generated-client` separately.

The root project's Python dependencies include the SDK runtime requirements (`httpx`, `pydantic`, `python-dateutil`, and `typing-extensions`); sync them if generation changes requirements.

**Important:** changing `swagger.json` alone does not change the installed SDK. Regenerate and rebuild/reinstall ceops.
