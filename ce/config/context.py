"""Named environment (context) management."""

from __future__ import annotations

import json
from typing import Optional

from pydantic import BaseModel, Field

from ce.config.settings import CONFIG_FILE, ensure_config_dir


class Environment(BaseModel):
    """A named Credential Engine deployment target."""

    label: str = Field(description="environment.")
    client_id: str = Field(description="Client ID.")
    device_auth_url: str = Field(description="Keycloak device authorization endpoint.")
    token_url: str = Field(description="Keycloak token endpoint.")
    scopes: str = Field(default="openid profile", description="Space-separated OIDC scopes.")
    publisher_base: str = Field(description="Publisher base URL (BFF for all API calls).")
    publisher_api_base: str = Field(
        default="",
        description="Publisher API base URL for API publishing (ce publisher).",
    )
    ssl_verify: bool = Field(default=True, description="Verify SSL certificates.")


class CLIConfig(BaseModel):
    """Top-level CLI config file model."""

    current_environment: Optional[str] = None
    environments: dict[str, Environment] = Field(default_factory=dict)


DEFAULT_ENVIRONMENTS: dict[str, Environment] = {
    "dev": Environment(
        label="Development",
        client_id="CE-CLI",
        device_auth_url="http://localhost:8080/realms/CE_Accounts/protocol/openid-connect/auth/device",
        token_url="http://localhost:8080/realms/CE_Accounts/protocol/openid-connect/token",
        scopes="openid profile",
        publisher_base="https://localhost:44330",
        publisher_api_base="http://localhost:8011",
        ssl_verify=False,
    ),
    "test": Environment(
        label="Test",
        client_id="CE-CLI",
        device_auth_url="https://login.test.credentialengine.org/realms/CE-Test/protocol/openid-connect/auth/device",
        token_url="https://login.test.credentialengine.org/realms/CE-Test/protocol/openid-connect/token",
        scopes="openid profile",
        publisher_base="https://sandbox.credentialengine.org/publisher",
        publisher_api_base="https://api.publisher.test.credentialengine.org",
        ssl_verify=True,
    ),
    "sandbox": Environment(
        label="Sandbox",
        client_id="CE-CLI",
        device_auth_url="https://login.sandbox.credentialengine.org/realms/CE-Sandbox/protocol/openid-connect/auth/device",
        token_url="https://login.sandbox.credentialengine.org/realms/CE-Sandbox/protocol/openid-connect/token",
        scopes="openid profile",
        publisher_base="https://sandbox.credentialengine.org/publisher",
        publisher_api_base="https://api.publisher.sandbox.credentialengine.org",
        ssl_verify=True,
    ),
    "prod": Environment(
        label="Production",
        client_id="CE-CLI",
        device_auth_url="https://login.credentialengine.org/realms/CE-Prod/protocol/openid-connect/auth/device",
        token_url="https://login.credentialengine.org/realms/CE-Prod/protocol/openid-connect/token",
        scopes="openid profile",
        publisher_base="https://apps.credentialengine.org/publisher",
        publisher_api_base="https://api.publisher.credentialengine.org",
        ssl_verify=True,
    ),
}


def _seed_environments(config: CLIConfig) -> tuple[CLIConfig, bool]:
    """Populate any missing default environments (non-destructive, never sets active)."""
    changed = False
    for name, env in DEFAULT_ENVIRONMENTS.items():
        if name not in config.environments:
            config.environments[name] = env
            changed = True
    return config, changed


def prompt_select_environment() -> str:
    """Interactively ask the user to pick an environment. Returns the chosen name."""
    from ce.utils.display import new_console, plain_table

    console = new_console()

    console.print()
    console.print("Welcome to the Credential Engine CLI!")
    console.print("Select the environment you want to connect to.")
    console.print("You can change this at any time with ce env use <name>")
    console.print()

    table = plain_table(["#", "Name", "Label", "Publisher base"])

    names = list(DEFAULT_ENVIRONMENTS.keys())
    for i, (name, env) in enumerate(DEFAULT_ENVIRONMENTS.items(), 1):
        table.add_row(str(i), f"{name}", env.label, env.publisher_base)

    console.print(table)

    while True:
        raw = console.input(
            "  Select environment (enter name or number, e.g. sandbox): "
        ).strip().lower()

        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(names):
                chosen = names[idx]
                break
            console.print(f"  Error: Please enter a number between 1 and {len(names)}.")
            continue

        if raw in DEFAULT_ENVIRONMENTS:
            chosen = raw
            break

        console.print(
            f"  Error: '{raw}' is not a valid environment. "
            f"Choose from: {', '.join(names)}."
        )

    env = DEFAULT_ENVIRONMENTS[chosen]
    console.print(f"\n  Environment set to {chosen} ({env.label}).\n")
    return chosen



def load_cli_config() -> CLIConfig:
  
    first_run = not CONFIG_FILE.exists()

    if first_run:
        config = CLIConfig()
        config, _ = _seed_environments(config)
        chosen = prompt_select_environment()
        config.current_environment = chosen
        save_cli_config(config)
        return config

    try:
        data = json.loads(CONFIG_FILE.read_text())
        config = CLIConfig(**data)
    except Exception:
        config = CLIConfig()

    config, changed = _seed_environments(config)
    if changed:
        save_cli_config(config)
    return config


def save_cli_config(config: CLIConfig) -> None:
    """Persist CLI config to disk."""
    ensure_config_dir()
    CONFIG_FILE.write_text(config.model_dump_json(indent=2))
    CONFIG_FILE.chmod(0o600)


def get_current_environment() -> Optional[tuple[str, Environment]]:
    """Return (name, Environment) for the active environment, or None."""
    config = load_cli_config()
    name = config.current_environment
    if name and name in config.environments:
        return name, config.environments[name]
    return None


def require_environment() -> tuple[str, Environment]:
    """Return the active environment or raise a UsageError."""
    import click
    result = get_current_environment()
    if result is None:
        raise click.UsageError(
            "No environment selected. Run 'ce env use <name>' to activate one."
        )
    return result