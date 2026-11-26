"""Select and inspect built-in Credential Engine environments."""

from __future__ import annotations

import click

from ce.config.context import load_cli_config, save_cli_config
from ce.config.environment import DEFAULT_ENVIRONMENTS, ENV_NAMES
from ce.utils.display import new_console, print_pairs

console = new_console()
_ENV_NAMES = ENV_NAMES
_ENV_CHOICE = click.Choice(_ENV_NAMES, case_sensitive=False)


@click.group("env")
def env_group() -> None:
    """Select or inspect a Credential Engine environment."""


@env_group.command("list")
def env_list() -> None:
    """List valid environment names."""
    active = load_cli_config().current_environment
    for name in _ENV_NAMES:
        marker = "*" if name == active else " "
        click.echo(f"{marker} {name}")


@env_group.command("use")
@click.argument("name", type=_ENV_CHOICE)
def env_use(name: str) -> None:
    """Select the active environment."""
    config = load_cli_config()
    config.current_environment = name
    save_cli_config(config)
    click.echo(f"Switched to {name}.")


@env_group.command("show")
@click.argument("name", type=_ENV_CHOICE, required=False)
@click.option(
    "--verbose", is_flag=True, help="Show detailed environment configuration."
)
def env_show(name: str | None, verbose: bool) -> None:
    """Show the active or explicitly named environment."""
    config = load_cli_config()
    target = name or config.current_environment
    if not target:
        click.echo("No environment selected. Run 'ce env use <name>'.")
        return
    if not verbose:
        click.echo(target)
        return
    env = DEFAULT_ENVIRONMENTS[target]
    print_pairs(
        console,
        [
            ("Name", target),
            ("Label", env.label),
            ("Active", str(target == config.current_environment)),
            ("Keycloak URL", env.keycloak_url),
            ("Realm", env.realm),
            ("Client ID", env.client_id),
            ("Device auth URL", env.device_auth_url),
            ("Token URL", env.token_url),
            ("Scopes", env.scopes),
            ("Publisher base (IIR)", env.publisher_base),
            ("Publisher API base", env.publisher_api_base),
            ("Consumer API base", env.consumer_api_base or "Not configured"),
            ("SSL verify", str(env.ssl_verify)),
        ],
    )
