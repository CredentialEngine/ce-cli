from unittest.mock import Mock

import click
import pytest

from ce.utils import errors, http

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "status,message",
    [
        (401, "Unauthorized"),
        (403, "Permission denied"),
        (404, "Not found"),
        (500, "API error"),
    ],
)
def test_error_messages(monkeypatch, status, message):
    console = Mock()
    monkeypatch.setattr(errors, "err_console", console)

    @errors.handle_api_errors
    def failing():
        raise http.APIError(status, "fixture")

    with pytest.raises(SystemExit) as exc:
        failing()
    assert exc.value.code == 1
    assert message in console.print.call_args.args[0]


def test_usage_error_preserved():
    @errors.handle_api_errors
    def failing():
        raise click.UsageError("missing argument")

    with pytest.raises(click.UsageError, match="missing argument"):
        failing()
