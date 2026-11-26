from __future__ import annotations

import re
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from ce.commands.env import env_group
from ce.config.context import DEFAULT_ENVIRONMENTS, CLIConfig

pytestmark = pytest.mark.unit


ANSI = re.compile(r"\x1b\[")


BOX_CHARS = re.compile("[─-▟]")


def assert_plain(text: str) -> None:
    assert not ANSI.search(text), f"colour or style codes in output: {text!r}"
    assert not BOX_CHARS.search(text), f"box characters in output: {text!r}"


def test_env_list_and_show_are_plain() -> None:
    config = CLIConfig(
        current_environment="sandbox", environments=dict(DEFAULT_ENVIRONMENTS)
    )
    runner = CliRunner()
    with patch("ce.commands.env.load_cli_config", return_value=config):
        listed = runner.invoke(env_group, ["list"])
        shown = runner.invoke(env_group, ["show", "sandbox"])

    assert listed.exit_code == 0, listed.output
    assert shown.exit_code == 0, shown.output
    assert_plain(listed.output)
    assert_plain(shown.output)
    assert "* " in listed.output
    assert shown.output.strip() == "sandbox"
