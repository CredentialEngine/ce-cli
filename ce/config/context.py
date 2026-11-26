"""Named environment (context) management."""

from __future__ import annotations

import json

from pydantic import BaseModel, Field

from ce.config.environment import DEFAULT_ENVIRONMENTS, Environment
from ce.config.settings import CONFIG_FILE, ensure_config_dir


class CLIConfig(BaseModel):
    """Top-level CLI config file model."""

    current_environment: str | None = None
    log_level: str | None = None
    environments: dict[str, Environment] = Field(default_factory=dict, exclude=True)


def load_cli_config() -> CLIConfig:
    """Resolve environment definitions from code, never from saved URLs."""
    name = None
    level = None
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            name = data.get("current_environment")
            level = data.get("log_level")
        except (OSError, ValueError, AttributeError):
            pass
    if not isinstance(name, str) or name not in DEFAULT_ENVIRONMENTS:
        name = None
    return CLIConfig(
        current_environment=name,
        log_level=level
        if level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        else None,
        environments={
            key: env.model_copy(deep=True) for key, env in DEFAULT_ENVIRONMENTS.items()
        },
    )


def save_cli_config(config: CLIConfig) -> None:
    """Persist the selected environment and logging preference, not service endpoints."""
    ensure_config_dir()
    CONFIG_FILE.write_text(config.model_dump_json(indent=2, exclude_none=True))
    CONFIG_FILE.chmod(0o600)


def get_current_environment() -> tuple[str, Environment] | None:
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
