"""Correct the IIR OpenAPI document before the client is generated.

Usage: python ce/iir/prepare_openapi.py ce/iir/openapi.json

The IIR API's Swagger says createChallenges answers a single `object`, but the API answers a list
of challenge objects. Left alone, the generated client cannot read a real answer. This script
fixes the document so the client is generated, not edited by hand. Remove a fix here once the IIR
API's own Swagger is correct.

It also keeps one request body type per operation. The IIR Swagger offers the same body as JSON, form,
text/json and XML. The generator cannot write XML or text/json, and when two supported types share one
schema it writes `body: X | X | Unset` and leaves `Unset` out of the imports, so the module fails to import
on Python 3.13 (3.14 evaluates annotations late and hides it). Form is kept because it is what the client
has always sent: the old client set both `json` and `data`, and httpx sends `data` (form) when both are given.
"""

import json
import sys

# (path, method, status) of each response that is really an array of the schema the spec gives.
ARRAY_RESPONSES = [("/iir-api/createChallenges", "post", "200")]

# The one request body type kept, when an operation offers it. Other types are removed from every operation.
KEPT_REQUEST_TYPE = "application/x-www-form-urlencoded"


def prepare(document: dict) -> int:
    changed = 0
    for path, method, status in ARRAY_RESPONSES:
        response = document["paths"][path][method]["responses"][status]
        for media in response["content"].values():
            schema = media["schema"]
            if schema.get("type") != "array":
                media["schema"] = {"type": "array", "items": schema}
                changed += 1
    changed += keep_one_request_type(document)
    return changed


def keep_one_request_type(document: dict) -> int:
    # Request bodies are written in the operation or shared under components.requestBodies.
    bodies = [
        operation.get("requestBody", {})
        for operations in document["paths"].values()
        for operation in operations.values()
        if isinstance(operation, dict)
    ]
    bodies += document.get("components", {}).get("requestBodies", {}).values()

    dropped = 0
    for body in bodies:
        content = body.get("content", {})
        if KEPT_REQUEST_TYPE not in content:
            continue
        for media_type in [name for name in content if name != KEPT_REQUEST_TYPE]:
            del content[media_type]
            dropped += 1
    return dropped


def main(path: str) -> None:
    with open(path, encoding="utf-8") as f:
        document = json.load(f)
    changed = prepare(document)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(document, f, indent=4)
        f.write("\n")
    print(f"{path}: {changed} change(s) made")


if __name__ == "__main__":
    main(sys.argv[1])
