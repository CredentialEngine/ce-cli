"""Correct the IIR OpenAPI document before the client is generated.

Usage: python ce/iir/prepare_openapi.py ce/iir/openapi.json

The IIR API's Swagger says createChallenges answers a single `object`, but the API answers a list
of challenge objects. Left alone, the generated client cannot read a real answer. This script
fixes the document so the client is generated, not edited by hand. Remove a fix here once the IIR
API's own Swagger is correct.
"""

import json
import sys

# (path, method, status) of each response that is really an array of the schema the spec gives.
ARRAY_RESPONSES = [("/iir-api/createChallenges", "post", "200")]


def prepare(document: dict) -> int:
    changed = 0
    for path, method, status in ARRAY_RESPONSES:
        response = document["paths"][path][method]["responses"][status]
        for media in response["content"].values():
            schema = media["schema"]
            if schema.get("type") != "array":
                media["schema"] = {"type": "array", "items": schema}
                changed += 1
    return changed


def main(path: str) -> None:
    with open(path, encoding="utf-8") as f:
        document = json.load(f)
    changed = prepare(document)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(document, f, indent=4)
        f.write("\n")
    print(f"{path}: {changed} schema(s) made arrays")


if __name__ == "__main__":
    main(sys.argv[1])
