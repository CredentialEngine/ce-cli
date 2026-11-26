import logging
from datetime import UTC, datetime

import pytest

from ce.utils import http
from ce.utils import logging as ce_logging


@pytest.fixture(autouse=True)
def reset_logging(monkeypatch):
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    names = (
        "azure",
        "httpx",
        "httpx2",
        "httpcore",
        "httpcore2",
        "authlib",
        "consumer_api_client",
        "publisher_client",
    )
    levels = {name: logging.getLogger(name).level for name in names}
    monkeypatch.setattr(ce_logging, "_CONFIGURED", False)
    monkeypatch.setenv("LOG_DESTINATIONS", "console")
    monkeypatch.delenv("LOG_FORMAT", raising=False)
    monkeypatch.delenv("AZURE_SDK_LOG_LEVEL", raising=False)
    yield
    for handler in root.handlers:
        if handler not in handlers:
            handler.close()
    root.handlers[:] = handlers
    root.setLevel(level)
    for name, previous in levels.items():
        logging.getLogger(name).setLevel(previous)


def test_timestamp():
    record = logging.LogRecord(
        "ce.test", logging.INFO, "test.py", 3, "message", (), None
    )
    record.created = datetime(2026, 11, 25, 12, 0, tzinfo=UTC).timestamp()
    assert (
        ce_logging.UtcFormatter("%(asctime)s %(message)s").format(record)
        == "2026-11-25T12:00:00.000Z message"
    )


def test_invalid_destination(monkeypatch):
    monkeypatch.setenv("LOG_DESTINATIONS", "invalid")
    with pytest.raises(ValueError, match="Unsupported log destination"):
        ce_logging.configure_logging()


def test_logging_configuration(monkeypatch):
    root = logging.getLogger()

    # Isolate loggers from pytest's logging handlers and the global logger cache.
    fake_root = logging.Logger("test-root")  # noqa: LOG001
    named = {}

    monkeypatch.setattr(
        logging,
        "getLogger",
        lambda name=None: (
            fake_root if name is None else named.setdefault(name, logging.Logger(name))  # noqa: LOG001
        ),
    )
    monkeypatch.setattr(ce_logging, "_CONFIGURED", False)
    monkeypatch.setenv("LOG_DESTINATIONS", "console")
    monkeypatch.setenv("AZURE_SDK_LOG_LEVEL", "WARNING")
    ce_logging.configure_logging(log_level="debug")
    assert fake_root.level == logging.DEBUG
    assert named["httpx2"].level == logging.WARNING
    handlers = fake_root.handlers[:]
    ce_logging.configure_logging(log_level="ERROR")
    assert fake_root.handlers == handlers and fake_root.level == logging.ERROR
    assert root is not fake_root
    with pytest.raises(ValueError, match="Invalid log level"):
        ce_logging.set_logging_level("unknown")


def test_logging_validation(monkeypatch):
    monkeypatch.delenv("CLOUDWATCH_LOG_GROUP", raising=False)
    monkeypatch.delenv("APPLICATIONINSIGHTS_CONNECTION_STRING", raising=False)
    for destination in ("cloudwatch", "azure", "unknown"):
        with pytest.raises(ValueError):
            ce_logging._build_handler(destination, logging.Formatter())
    with pytest.raises(ValueError, match="At least one"):
        ce_logging._parse_destinations(" , ")
    assert ce_logging._parse_destinations(" Console, AZURE ") == ["console", "azure"]


def test_exception_summary():
    exc = http.APIError(503, "example\nprivate details")
    result = ce_logging.summarize_exception(exc)
    assert "503" in result and "example" in result and "private details" not in result
    assert ce_logging.summarize_exception(ValueError("x" * 50), max_length=10).endswith(
        "..."
    )
    assert "INFO ce example" in ce_logging.format_status_line("example")
