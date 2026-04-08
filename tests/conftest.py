"""Shared pytest fixtures and markers."""

from __future__ import annotations

from unittest.mock import MagicMock
from pathlib import Path
from dotenv import load_dotenv


import pytest

load_dotenv(Path(__file__).resolve().parents[1] / ".env.test")

import os

PUBLISHER_BASE = os.getenv("CE_PUBLISHER_BASE", "https://localhost:44330")
ACCESS_TOKEN = os.getenv("CE_TEST_ACCESS_TOKEN", "")
USER_ID = os.getenv("CE_TEST_USER_ID", "")
CTID = os.getenv("CE_TEST_CTID", "")
CHALLENGE_UUID = os.getenv("CE_TEST_CHALLENGE_UUID", "")

ED25519_PRIVATE_MULTIBASE = os.getenv("CE_TEST_PRIVKEY_MULTIBASE", "")
ED25519_DID_KEY = os.getenv("CE_TEST_DID_KEY", "")

ED25519_KID = (
    f"{ED25519_DID_KEY}#{ED25519_DID_KEY[len('did:key:'):]}"
    if ED25519_DID_KEY.startswith("did:key:")
    else ""
)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "unit: mark test as a unit test",
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test requiring a live server",
    )


@pytest.fixture
def mock_env():
    env = MagicMock()
    env.publisher_base = PUBLISHER_BASE
    env.ssl_verify = False
    return env
