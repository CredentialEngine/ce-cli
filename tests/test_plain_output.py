"""The CLI prints plain text: no boxes, no colours. Spinners are the only decoration.

Run with:
    pytest -m unit tests/test_plain_output.py
"""

from __future__ import annotations

import io
import json
import re
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from rich.console import Console

from ce.commands.env import env_group
from ce.config.context import CLIConfig, DEFAULT_ENVIRONMENTS
from ce.utils.display import new_console, plain_table, print_pairs
from ce.utils.output import print_output

pytestmark = pytest.mark.unit

ANSI = re.compile(r"\x1b\[")
# Box-drawing and block characters: what Rich uses for borders and panels.
BOX_CHARS = re.compile("[─-▟]")

CE_SOURCE = Path(__file__).resolve().parent.parent / "ce"
# Rich pieces that draw boxes or colour text. The generated clients under ce/iir/api are not ours to scan.
FORBIDDEN = ("rich.panel", "rich.syntax", "rich.box", "box.SIMPLE", "border_style", "header_style=\"bold\"")


def terminal_console(buffer: io.StringIO) -> Console:
    """A console that behaves like a colour terminal, so any styling would show up as escape codes."""
    return Console(file=buffer, force_terminal=True, color_system="truecolor", width=100, highlight=False)


def assert_plain(text: str) -> None:
    assert not ANSI.search(text), f"colour or style codes in output: {text!r}"
    assert not BOX_CHARS.search(text), f"box characters in output: {text!r}"


def test_plain_table_has_no_borders_or_styles() -> None:
    buffer = io.StringIO()
    table = plain_table(["Name", "Label"])
    table.add_row("sandbox", "Sandbox")
    terminal_console(buffer).print(table)

    text = buffer.getvalue()
    assert_plain(text)
    assert "Name" in text and "sandbox" in text


def test_plain_table_honours_column_widths() -> None:
    buffer = io.StringIO()
    table = plain_table(["#", "CTID"], widths=[4, 10])
    table.add_row("1", "ce-aaaaaaaaaaaaaaaaaaaa")
    terminal_console(buffer).print(table)

    text = buffer.getvalue()
    assert_plain(text)
    # The CTID column is 10 wide, so the value folds onto several lines instead of widening the table.
    assert "ce-aaaaaaaaaaaaaaaaaaaa" not in text
    assert text.replace("\n", "").replace(" ", "").endswith("ce-aaaaaaaaaaaaaaaaaaaa")


def test_the_console_prints_markup_and_numbers_as_written() -> None:
    buffer = io.StringIO()
    console = new_console()
    console.file = buffer
    console.print("[bold]kept as typed[/bold] 42 https://example.org/a")

    assert buffer.getvalue() == "[bold]kept as typed[/bold] 42 https://example.org/a\n"


def test_print_pairs_aligns_values_without_styling() -> None:
    buffer = io.StringIO()
    console = new_console()
    console.file = buffer
    print_pairs(console, [("Name", "x"), ("Publisher base", "y")])

    assert buffer.getvalue().splitlines() == ["Name:            x", "Publisher base:  y"]


def test_json_output_is_plain_json(capsys: pytest.CaptureFixture[str]) -> None:
    print_output([{"id": 1, "name": "a"}], "json")

    out = capsys.readouterr().out
    assert_plain(out)
    assert json.loads(out) == [{"id": 1, "name": "a"}]


def test_table_output_is_plain(capsys: pytest.CaptureFixture[str]) -> None:
    print_output([{"id": 1, "name": "a"}], "table", columns=["id", "name"], title="Projects")

    out = capsys.readouterr().out
    assert_plain(out)
    assert "Projects" in out and "Id" in out and "Name" in out


def test_env_list_and_show_are_plain() -> None:
    config = CLIConfig(current_environment="sandbox", environments=dict(DEFAULT_ENVIRONMENTS))
    runner = CliRunner()
    with patch("ce.commands.env.load_cli_config", return_value=config):
        listed = runner.invoke(env_group, ["list"])
        shown = runner.invoke(env_group, ["show", "sandbox"])

    assert listed.exit_code == 0, listed.output
    assert shown.exit_code == 0, shown.output
    assert_plain(listed.output)
    assert_plain(shown.output)
    assert "* " in listed.output
    assert "Environment: sandbox" in shown.output


@pytest.mark.parametrize("forbidden", FORBIDDEN)
def test_the_source_has_no_boxes_or_bold_headers(forbidden: str) -> None:
    offenders = [
        path.relative_to(CE_SOURCE).as_posix()
        for path in CE_SOURCE.rglob("*.py")
        if "iir/api" not in path.as_posix() and forbidden in path.read_text(encoding="utf-8")
    ]
    assert offenders == [], f"{forbidden!r} found in {offenders}"
