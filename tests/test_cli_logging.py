"""Logging and version banner contract shared with ceops."""

import logging
from datetime import UTC, datetime
from inspect import signature

import click
import pytest
from click.testing import CliRunner

from ce import __version__
from ce.utils import logging as ce_logging
from ce.utils.cli_logging import VersionedGroup


def separate_runner():
    return CliRunner(
        **(
            {"mix_stderr": False}
            if "mix_stderr" in signature(CliRunner).parameters
            else {}
        )
    )


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


def test_persistent_logging(tmp_path, monkeypatch):
    from ce.commands.logging import logging_group
    from ce.config import context

    monkeypatch.setattr(context, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(context, "ensure_config_dir", lambda: None)
    runner = CliRunner()
    assert runner.invoke(logging_group, ["show"]).output.strip() == "WARNING"
    assert runner.invoke(logging_group, ["set", "log-level", "debug"]).exit_code == 0
    assert context.load_cli_config().log_level == "DEBUG"
    assert runner.invoke(logging_group, ["show"]).output.strip() == "DEBUG"
    assert runner.invoke(logging_group, ["set", "log-level", "TRACE"]).exit_code == 2


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


def test_version_banner_and_leaf_version():
    @click.group(cls=VersionedGroup)
    @click.version_option(__version__, prog_name="ce")
    def root():
        pass

    @root.command()
    @click.option("--version", default="latest")
    def show(version):
        click.echo(version)

    runner = separate_runner()
    result = runner.invoke(root, ["--version"])
    assert result.exit_code == 0
    assert result.stdout == f"ce, version {__version__}\n"
    assert not result.stderr
    result = runner.invoke(root, ["show", "--version", "2026-11-25"])
    assert result.exit_code == 0
    assert result.stdout == "2026-11-25\n"
    assert result.stderr == f"ce, version {__version__}\n"
    assert runner.invoke(root, ["show", "--log-level", "DEBUG"]).exit_code == 2
