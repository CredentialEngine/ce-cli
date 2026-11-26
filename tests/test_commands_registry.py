import pytest
from click.testing import CliRunner

from ce.commands.registry import registry_group


@pytest.mark.parametrize("option", ["--registry-url", "--consumer-url"])
def test_registry_rejects_url_override(option):
    result = CliRunner().invoke(
        registry_group, [option, "https://untrusted.example", "downloads", "show"]
    )
    assert result.exit_code == 2
    assert "No such option" in result.output
