from __future__ import annotations

import json
import re
from unittest.mock import Mock

import pytest

from ce.utils import output
from ce.utils.output import print_output

pytestmark = pytest.mark.unit


ANSI = re.compile(r"\x1b\[")


BOX_CHARS = re.compile("[─-▟]")


def assert_plain(text: str) -> None:
    assert not ANSI.search(text), f"colour or style codes in output: {text!r}"
    assert not BOX_CHARS.search(text), f"box characters in output: {text!r}"


def test_json_output_is_plain_json(capsys: pytest.CaptureFixture[str]) -> None:
    print_output([{"id": 1, "name": "a"}], "json")

    out = capsys.readouterr().out
    assert_plain(out)
    assert json.loads(out) == [{"id": 1, "name": "a"}]


def test_table_output_is_plain(capsys: pytest.CaptureFixture[str]) -> None:
    print_output(
        [{"id": 1, "name": "a"}], "table", columns=["id", "name"], title="Projects"
    )

    out = capsys.readouterr().out
    assert_plain(out)
    assert "Projects" in out and "Id" in out and "Name" in out


@pytest.mark.parametrize("fmt", ["json", "tsv", "none", "table", "yaml"])
def test_output_formats(monkeypatch, capsys, fmt):
    console = Mock()
    monkeypatch.setattr(output, "console", console)
    output.print_output(
        [{"name": "Nursing", "count": 3}],
        fmt,
        columns=["name", "count"],
        title="Results",
    )
    text = capsys.readouterr().out
    if fmt == "json":
        assert json.loads(text) == [{"name": "Nursing", "count": 3}]
    elif fmt == "tsv":
        assert text == "Nursing\t3\n"
    elif fmt == "yaml":
        assert "Nursing" in text
    elif fmt == "table":
        console.print.assert_any_call("Results")
    else:
        assert not text
        console.print.assert_not_called()


@pytest.mark.parametrize(
    "data,expected",
    [
        ({"a": 1}, [{"a": 1}]),
        (2, [{"value": 2}]),
        ([1, 2], [{"value": 1}, {"value": 2}]),
    ],
)
def test_output_normalization(data, expected):
    assert output._to_rows(data) == expected
