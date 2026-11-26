from contextlib import nullcontext
from unittest.mock import Mock

import httpx2
import pytest
from click.testing import CliRunner

from ce import __version__
from ce.commands import version

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "response,expected",
    [
        (httpx2.Response(200, json={"info": {"version": __version__}}), "up to date"),
        (httpx2.Response(200, json={"info": {"version": "9999.1.1"}}), "newer version"),
        (httpx2.Response(503), "Could not reach PyPI"),
        (httpx2.Response(200, json={}), "Update check failed"),
    ],
)
def test_version_check(monkeypatch, response, expected):
    console = Mock()
    console.status.return_value = nullcontext()
    monkeypatch.setattr(version, "console", console)
    get = Mock(return_value=response)
    monkeypatch.setattr(httpx2, "get", get)
    assert CliRunner().invoke(version.version_command, ["--check"]).exit_code == 0
    assert expected in str(console.print.call_args.args[0])
    assert get.call_args.kwargs["headers"]["User-Agent"] == version.USER_AGENT
