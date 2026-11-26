"""Built-in environment selection is noninteractive and hides endpoints."""

import json
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner

from ce.commands.env import env_group
from ce.config import context


@pytest.fixture
def config_path(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    monkeypatch.setattr(context, "CONFIG_FILE", path)
    monkeypatch.setattr(context, "ensure_config_dir", lambda: None)
    return path


def test_list_first_run(config_path):
    with patch(
        "rich.console.Console.input", side_effect=AssertionError("Unexpected prompt")
    ):
        result = CliRunner().invoke(env_group, ["list"])
    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == ["  dev", "  test", "  sandbox", "  prod"]
    assert not config_path.exists()
    assert context.get_current_environment() is None


def test_use_persists_only_selection(config_path):
    runner = CliRunner()
    result = runner.invoke(env_group, ["use", "sandbox"])
    assert result.exit_code == 0, result.output
    assert context.require_environment()[0] == "sandbox"
    assert json.loads(config_path.read_text()) == {"current_environment": "sandbox"}
    assert runner.invoke(env_group, ["list"]).output.splitlines() == [
        "  dev",
        "  test",
        "* sandbox",
        "  prod",
    ]
    assert runner.invoke(env_group, ["show"]).output == "sandbox\n"


def test_missing_environment_returns_error(config_path):
    with pytest.raises(click.UsageError, match="ce env use"):
        context.require_environment()


def test_legacy_urls_are_ignored(config_path):
    config_path.write_text(
        json.dumps(
            {
                "current_environment": "dev",
                "environments": {
                    "dev": {"publisher_base": "https://old.invalid"},
                    "custom": {},
                },
            }
        )
    )
    original = config_path.read_bytes()
    name, env = context.require_environment()
    assert name == "dev"
    assert env.publisher_base == context.DEFAULT_ENVIRONMENTS["dev"].publisher_base
    assert set(context.load_cli_config().environments) == set(
        context.DEFAULT_ENVIRONMENTS
    )
    assert config_path.read_bytes() == original


def test_invalid_name_rejected(config_path):
    assert CliRunner().invoke(env_group, ["use", "custom"]).exit_code == 2
    assert not config_path.exists()


def test_details_are_explicit(config_path):
    runner = CliRunner()
    assert runner.invoke(env_group, ["show", "dev"]).output == "dev\n"
    with patch("ce.commands.env.print_pairs") as pairs:
        result = runner.invoke(env_group, ["show", "dev", "--verbose"])
    assert result.exit_code == 0, result.output
    details = dict(pairs.call_args.args[1])
    assert (
        details["Publisher API base"]
        == context.DEFAULT_ENVIRONMENTS["dev"].publisher_api_base
    )
    assert (
        details["Consumer API base"]
        == context.DEFAULT_ENVIRONMENTS["dev"].consumer_api_base
    )
    assert (
        details["Device auth URL"]
        == context.DEFAULT_ENVIRONMENTS["dev"].device_auth_url
    )


@pytest.mark.parametrize(
    "name,base,realm",
    [
        ("dev", "https://localhost:8443", "CE-Dev"),
        ("test", "https://login.test.credentialengine.org", "CE-Test"),
        ("sandbox", "https://login.sandbox.credentialengine.org", "CE-Sandbox"),
        ("prod", "https://login.credentialengine.org", "CE-Prod"),
    ],
)
def test_keycloak_endpoints(config_path, name, base, realm):
    from ce.config.environment import DEFAULT_ENVIRONMENTS

    env = context.load_cli_config().environments[name]
    assert env.keycloak_url == base
    assert env.realm == realm
    assert env.client_id == "ce-cli"
    assert (
        env.device_auth_url
        == f"{base}/realms/{realm}/protocol/openid-connect/auth/device"
    )
    assert env.token_url == f"{base}/realms/{realm}/protocol/openid-connect/token"
    assert context.DEFAULT_ENVIRONMENTS is DEFAULT_ENVIRONMENTS


def test_oidc_settings_use_active_environment(config_path):
    from ce.config.settings import load_oidc_settings

    config = context.load_cli_config()
    config.current_environment = "dev"
    context.save_cli_config(config)
    settings = load_oidc_settings()
    env = context.require_environment()[1]
    assert settings.issuer == env.issuer
    assert settings.token_endpoint == env.token_url
    assert settings.device_authorization_endpoint == env.device_auth_url
    assert settings.client_id == env.client_id


@pytest.mark.parametrize(
    "name,base",
    [
        ("dev", "https://localhost:7079"),
        ("test", "https://api.consumer.test.credentialengine.org"),
        ("sandbox", "https://api.consumer.sandbox.credentialengine.org"),
        ("prod", "https://api.consumer.credentialengine.org"),
    ],
)
def test_consumer_api_base(config_path, name, base):
    env = context.load_cli_config().environments[name]
    assert env.consumer_api_base == base
    assert not hasattr(env, "registry_api_base")
