"""Shared pytest fixtures and markers."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env.test")

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
    config.addinivalue_line(
        "markers",
        "vcr: mark test as using recorded HTTP interactions (pytest-recording)",
    )


@pytest.fixture
def mock_env():
    env = MagicMock()
    env.publisher_base = PUBLISHER_BASE
    env.ssl_verify = False
    return env




@pytest.fixture(scope="session")
def vcr_config():
    return {
        "filter_headers": [
            ("authorization", "REDACTED"),
            ("cookie", "REDACTED"),
            ("x-api-key", "REDACTED"),
        ],
        "filter_query_parameters": [
            ("access_token", "REDACTED"),
            ("token", "REDACTED"),
        ],
        "filter_post_data_parameters": [
            ("access_token", "REDACTED"),
            ("client_secret", "REDACTED"),
        ],
        "match_on": ["method", "scheme", "host", "port", "path", "query"],
        "record_mode": os.getenv("VCR_RECORD_MODE", "none"),
    }


@pytest.fixture(scope="module")
def vcr_cassette_dir(request):
    """Store cassettes alongside the test module under a 'cassettes/' folder."""
    return str(Path(request.module.__file__).parent / "cassettes")