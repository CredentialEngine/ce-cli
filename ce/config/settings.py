"""Configuration management for the Credential Engine CLI."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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


class OIDCSettings(BaseSettings):
    """Keycloak / OIDC connection settings.

    These can be overridden by environment variables prefixed with CE_.

    Example .env or shell exports::

        CE_OIDC_ISSUER=https://auth.example.com/realms/myrealm
        CE_OIDC_CLIENT_ID=ce-cli
    """

    model_config = SettingsConfigDict(
        env_prefix="CE_OIDC_",
        env_file=str(CONFIG_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    issuer: str = Field(
        default="https://auth.example.com/realms/credential-engine",
        description="Keycloak realm issuer URL.",
    )
    client_id: str = Field(
        default="ce-cli",
        description="OIDC public client ID registered in Keycloak.",
    )
    scopes: str = Field(default="openid profile email offline_access")


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
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_at: Optional[float] = None   # Unix timestamp
    scope: Optional[str] = None


def ensure_config_dir() -> None:
    """Create the CE config directory with safe permissions."""
    CONFIG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)


def load_tokens() -> Optional[StoredTokens]:
    """Load stored tokens from disk, or return None if not present."""
    if not TOKEN_FILE.exists():
        return None
    try:
        data = json.loads(TOKEN_FILE.read_text())
        return StoredTokens(**data)
    except Exception:
        return None


def save_tokens(tokens: StoredTokens) -> None:
    """Persist tokens to disk with restrictive permissions."""
    ensure_config_dir()
    TOKEN_FILE.write_text(tokens.model_dump_json(indent=2))
    TOKEN_FILE.chmod(0o600)


def delete_tokens() -> None:
    """Remove stored tokens from disk."""
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()


def load_oidc_settings() -> OIDCSettings:
    """Return OIDC settings, layering env vars over defaults."""
    return OIDCSettings()
