"""Prepare the Publisher's Swagger document for openapi-python-client.

    python ce/publisher/prepare_openapi.py ce/publisher/swagger.json ce/publisher/openapi.json

The Publisher lists text/plain, application/json and text/json for every
JSON answer and request. The generator takes the first one, so it would read
JSON answers as text. This keeps application/json wherever it is offered.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

JSON_CONTENT_TYPE = "application/json"


def keep_json_content(document: dict[str, Any]) -> dict[str, Any]:
    """Return the document with only application/json where a body offers it."""
    for operations in document.get("paths", {}).values():
        for operation in operations.values():
            if not isinstance(operation, dict):
                continue
            _keep_json(operation.get("requestBody"))
            for response in operation.get("responses", {}).values():
                _keep_json(response)
    return document


def _keep_json(body: Any) -> None:
    if not isinstance(body, dict):
        return
    content = body.get("content")
    if isinstance(content, dict) and JSON_CONTENT_TYPE in content:
        body["content"] = {JSON_CONTENT_TYPE: content[JSON_CONTENT_TYPE]}


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    source, target = Path(argv[1]), Path(argv[2])
    document = json.loads(source.read_text(encoding="utf-8"))
    target.write_text(
        json.dumps(keep_json_content(document), indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
