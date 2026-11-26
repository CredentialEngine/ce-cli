"""Configuration management for the Credential Engine CLI."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


def _config_dir() -> Path:
    """Return the CE config directory, honouring $CE_CONFIG_DIR override."""
    override = os.environ.get("CE_CONFIG_DIR")
    if override:
        return Path(override)
    return Path.home() / ".ce"


CONFIG_DIR = _config_dir()
CONFIG_FILE = CONFIG_DIR / "config.json"
TOKEN_FILE = CONFIG_DIR / "tokens.json"


class OIDCSettings(BaseModel):
    """Compatibility view of the active environment's OIDC settings."""

    issuer: str
    client_id: str
    scopes: str

    @property
    def device_authorization_endpoint(self) -> str:
        return f"{self.issuer.rstrip('/')}/protocol/openid-connect/auth/device"

    @property
    def token_endpoint(self) -> str:
        return f"{self.issuer.rstrip('/')}/protocol/openid-connect/token"

    @property
    def userinfo_endpoint(self) -> str:
        return f"{self.issuer.rstrip('/')}/protocol/openid-connect/userinfo"

    @property
    def end_session_endpoint(self) -> str:
        return f"{self.issuer.rstrip('/')}/protocol/openid-connect/logout"


class StoredTokens(BaseModel):
    """OIDC tokens persisted to disk."""

    access_token: str
    refresh_token: str | None = None
    id_token: str | None = None
    token_type: str = "Bearer"
    expires_at: float | None = None  # Unix timestamp
    scope: str | None = None


def ensure_config_dir() -> None:
    """Create the CE config directory with safe permissions."""
    CONFIG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)


def _current_environment_name() -> str | None:
    """The active environment's name, or None when none is selected."""
    from ce.config.context import get_current_environment

    result = get_current_environment()
    return result[0] if result else None


def token_file(env_name: str | None = None) -> Path:
    """The file that holds one environment's tokens (the active environment by default).

    Each environment has its own file, so a session for one environment is
    never sent to, or mistaken for, another.
    """
    name = env_name or _current_environment_name()
    if not name:
        return TOKEN_FILE
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return CONFIG_DIR / f"tokens-{safe}.json"


def _adopt_legacy_tokens(env_name: str | None, path: Path) -> None:
    """Move tokens saved before tokens were kept per environment to the active environment's file."""
    if path == TOKEN_FILE or path.exists() or not TOKEN_FILE.exists():
        return
    if env_name is None or env_name == _current_environment_name():
        TOKEN_FILE.replace(path)


def load_tokens(env_name: str | None = None) -> StoredTokens | None:
    """Load an environment's stored tokens (the active environment by default), or None if not present."""
    path = token_file(env_name)
    _adopt_legacy_tokens(env_name, path)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return StoredTokens(**data)
    except (OSError, ValueError, TypeError):
        return None


def save_tokens(tokens: StoredTokens, env_name: str | None = None) -> None:
    """Persist an environment's tokens to disk with restrictive permissions."""
    ensure_config_dir()
    path = token_file(env_name)
    path.write_text(tokens.model_dump_json(indent=2))
    path.chmod(0o600)


def delete_tokens(env_name: str | None = None) -> None:
    """Remove an environment's stored tokens from disk."""
    path = token_file(env_name)
    _adopt_legacy_tokens(env_name, path)
    if path.exists():
        path.unlink()


def load_oidc_settings() -> OIDCSettings:
    """Return OIDC settings from the same environment used by login."""
    from ce.config.context import require_environment

    _, env = require_environment()
    return OIDCSettings(issuer=env.issuer, client_id=env.client_id, scopes=env.scopes)
