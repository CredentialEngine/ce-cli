"""Static deployment configuration shared by authentication and API clients."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Environment(BaseModel):
    """A named Credential Engine deployment target."""

    label: str = Field(description="environment.")
    client_id: str = Field(description="Client ID.")
    keycloak_url: str = Field(description="Keycloak base URL.")
    realm: str = Field(description="Keycloak realm.")

    @property
    def issuer(self) -> str:
        return f"{self.keycloak_url.rstrip('/')}/realms/{self.realm}"

    @property
    def device_auth_url(self) -> str:
        return f"{self.issuer}/protocol/openid-connect/auth/device"

    @property
    def token_url(self) -> str:
        return f"{self.issuer}/protocol/openid-connect/token"

    @property
    def userinfo_url(self) -> str:
        return f"{self.issuer}/protocol/openid-connect/userinfo"

    @property
    def revoke_url(self) -> str:
        return f"{self.issuer}/protocol/openid-connect/revoke"

    scopes: str = Field(
        default="openid profile email", description="Space-separated OIDC scopes."
    )
    publisher_base: str = Field(
        description="Publisher base URL (BFF for all API calls)."
    )
    publisher_api_base: str = Field(
        default="",
        description="Publisher API base URL for API publishing (ce publisher).",
    )
    consumer_api_base: str = Field(default="", description="Consumer API base URL.")
    ssl_verify: bool = Field(default=True, description="Verify SSL certificates.")


DEFAULT_ENVIRONMENTS: dict[str, Environment] = {
    "dev": Environment(
        label="Development",
        client_id="ce-cli",
        keycloak_url="https://localhost:8443",
        realm="CE-Dev",
        scopes="openid profile email",
        publisher_base="https://localhost:44330",
        publisher_api_base="http://localhost:8011",
        consumer_api_base="https://localhost:7079",
        ssl_verify=False,
    ),
    "test": Environment(
        label="Test",
        client_id="ce-cli",
        keycloak_url="https://login.test.credentialengine.org",
        realm="CE-Test",
        scopes="openid profile email",
        publisher_base="https://sandbox.credentialengine.org/publisher",
        publisher_api_base="https://api.publisher.test.credentialengine.org",
        consumer_api_base="https://api.consumer.test.credentialengine.org",
        ssl_verify=True,
    ),
    "sandbox": Environment(
        label="Sandbox",
        client_id="ce-cli",
        keycloak_url="https://login.sandbox.credentialengine.org",
        realm="CE-Sandbox",
        scopes="openid profile email",
        publisher_base="https://sandbox.credentialengine.org/publisher",
        publisher_api_base="https://api.publisher.sandbox.credentialengine.org",
        consumer_api_base="https://api.consumer.sandbox.credentialengine.org",
        ssl_verify=True,
    ),
    "prod": Environment(
        label="Production",
        client_id="ce-cli",
        keycloak_url="https://login.credentialengine.org",
        realm="CE-Prod",
        scopes="openid profile email",
        publisher_base="https://apps.credentialengine.org/publisher",
        publisher_api_base="https://api.publisher.credentialengine.org",
        consumer_api_base="https://api.consumer.credentialengine.org",
        ssl_verify=True,
    ),
}

ENV_NAMES = tuple(DEFAULT_ENVIRONMENTS)
