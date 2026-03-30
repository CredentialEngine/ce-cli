"""Shared pytest fixtures and markers."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test requiring a live server",
    )


SWAGGER = {
    "swagger": "2.0",
    "info": {"version": "v1", "title": "CTI Directory API"},
    "host": "localhost:44330",
    "schemes": ["https"],
    "paths": {
        "/api/iir/isUserAMember":     {"get":  {"operationId": "IIRApi_IsUserAMember"}},
        "/api/iir/getRegistryResource":{"get": {"operationId": "IIRApi_GetRegistryResource"}},
        "/api/iir/validateDidWeb":    {"get":  {"operationId": "IIRApi_ValidateWeb"}},
        "/api/iir/validateDidKey":    {"get":  {"operationId": "IIRApi_ValidateKey"}},
        "/api/iir/createChallenges":  {"post": {"operationId": "IIRApi_CreateChallenges"}},
        "/api/iir/validateJwt":       {"post": {"operationId": "IIRApi_ValidateJwtSignature"}},
        "/api/iir/saveChallengeToken":{"post": {"operationId": "IIRApi_SaveChallengeToken"}},
        "/api/iir/submitToIIR":       {"post": {"operationId": "IIRApi_SubmitToIIR"}},
    },
}


@pytest.fixture(autouse=True)
def patch_swagger(tmp_path, monkeypatch):
    """
    Write a real swagger.json to a temp dir and point _SWAGGER_FILE at it.
    Also clears lru_cache so each test gets a fresh load.
    """
    import ce.iir.did_ops as did_ops

    swagger_file = tmp_path / "swagger.json"
    swagger_file.write_text(json.dumps(SWAGGER))

    monkeypatch.setattr(did_ops, "_SWAGGER_FILE", swagger_file)
    did_ops._load_swagger.cache_clear()
    did_ops._path_index.cache_clear()

    yield

    did_ops._load_swagger.cache_clear()
    did_ops._path_index.cache_clear()



PUBLISHER_BASE = "https://localhost:44330"
ACCESS_TOKEN   = "fake.access.token"
USER_ID        = "550e8400-e29b-41d4-a716-446655440000"
CTID           = "ce-12345678-1234-1234-1234-123456789abc"
CHALLENGE_UUID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


ED25519_PRIVATE_MULTIBASE = "z3u2en7t5LR2WtQH5PfFqMqwVHBeXouLzo6haApm8XHqvjxdqoJnAkunJQQBCpRXuJpMKNPdEMeRHBHBUkUHYFa8"
ED25519_DID_KEY           = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
ED25519_KID               = f"{ED25519_DID_KEY}#{ED25519_DID_KEY[len('did:key:'):]}"


@pytest.fixture
def mock_env():
    env = MagicMock()
    env.publisher_base = PUBLISHER_BASE
    env.ssl_verify = False
    return env
