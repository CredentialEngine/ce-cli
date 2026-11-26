"""Keycloak Device Authorization Grant flow"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import httpx2
from authlib.common.security import generate_token
from authlib.integrations.base_client.errors import OAuthError
from authlib.integrations.httpx_client import OAuth2Client
from authlib.oauth2.rfc6749.errors import OAuth2Error
from authlib.oauth2.rfc7636 import create_s256_code_challenge

from ce.utils.user_agent import USER_AGENT

if TYPE_CHECKING:
    from ce.config.environment import Environment
    from ce.config.settings import StoredTokens

DEVICE_CODE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"


@dataclass
class DeviceAuthResponse:
    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str | None
    expires_in: int
    interval: int


@dataclass
class TokenResponse:
    access_token: str
    refresh_token: str | None
    id_token: str | None
    token_type: str
    expires_in: int
    scope: str | None


class DeviceFlowError(Exception):
    """Raised when the device flow cannot complete."""


class AuthorizationPendingError(DeviceFlowError):
    """User has not yet approved, keep polling."""


class SlowDownError(DeviceFlowError):
    """Server requested a longer polling interval."""


class AccessDeniedError(DeviceFlowError):
    """User denied the authorization request."""


class TokenExpiredError(DeviceFlowError):
    """Device code expired before the user approved."""


class ClientConfigurationError(DeviceFlowError):
    """Keycloak rejected the configured OAuth client, not the user session."""


class RefreshRejectedError(DeviceFlowError):
    """Keycloak refused the refresh token: the session ended or the token expired.

    Only signing in again helps. Other DeviceFlowErrors from a refresh (the
    server could not be reached, or answered with a server error) may pass.
    """


def create_pkce_pair() -> tuple[str, str]:
    """Return a new PKCE code verifier and its S256 challenge (RFC 7636)."""
    verifier = generate_token(64)
    return verifier, create_s256_code_challenge(verifier)


class KeycloakDeviceFlowClient:
    """Keycloak device authorization grant."""

    def __init__(
        self,
        env: Environment,
        transport: httpx2.BaseTransport | None = None,
    ) -> None:
        self._env = env
        self._http = httpx2.Client(
            timeout=30,
            verify=env.ssl_verify,
            transport=transport,
            headers={"User-Agent": USER_AGENT},
        )
        # Token grants (the device code and the refresh) go through Authlib, which sends the
        # form, reads the answer and decodes OAuth errors. ce-cli is a public client: no secret.
        self._oauth = OAuth2Client(
            client_id=env.client_id,
            token_endpoint_auth_method="none",
            timeout=30,
            verify=env.ssl_verify,
            transport=transport,
            headers={"User-Agent": USER_AGENT},
        )
        # The verifier of the device code being waited on, so a token can only
        # be collected by the process that started the sign-in.
        self._device_pkce: tuple[str, str] | None = None

    def request_device_code(self) -> DeviceAuthResponse:
        self._device_pkce = None
        verifier, challenge = create_pkce_pair()

        resp = self._post(
            self._env.device_auth_url,
            {
                "client_id": self._env.client_id,
                "scope": self._env.scopes,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
            "Device authorization request",
        )
        if resp.is_error and self._oauth_error_code(resp) in (
            "invalid_client",
            "unauthorized_client",
        ):
            raise ClientConfigurationError(self._client_error_message())
        self._raise_for_status(resp)
        body = self._json(resp, "Device authorization request")
        self._device_pkce = (body["device_code"], verifier)

        return DeviceAuthResponse(
            device_code=body["device_code"],
            user_code=body["user_code"],
            verification_uri=body["verification_uri"],
            verification_uri_complete=body.get("verification_uri_complete"),
            expires_in=body.get("expires_in", 600),
            interval=body.get("interval", 5),
        )

    def poll_for_token(
        self,
        device_code: str,
        interval: int,
        expires_in: int,
        on_pending: callable | None = None,
    ) -> TokenResponse:
        deadline = time.monotonic() + expires_in
        poll_interval = interval

        extra: dict[str, str] = {}
        if self._device_pkce is not None:
            pkce_device_code, verifier = self._device_pkce
            if pkce_device_code != device_code:
                raise DeviceFlowError(
                    "Device code does not match the pending PKCE session."
                )
            extra["code_verifier"] = verifier

        while time.monotonic() < deadline:
            time.sleep(poll_interval)

            try:
                body = self._oauth.fetch_token(
                    self._env.token_url,
                    grant_type=DEVICE_CODE_GRANT,
                    device_code=device_code,
                    **extra,
                )
            except (OAuthError, OAuth2Error) as exc:
                error = exc.error
                if error == "authorization_pending":
                    if on_pending:
                        on_pending()
                    continue
                if error == "slow_down":
                    poll_interval += 5
                    if on_pending:
                        on_pending()
                    continue
                if error == "access_denied":
                    raise AccessDeniedError(
                        "Authorization was denied by the user."
                    ) from exc
                if error in ("expired_token", "device_code_expired"):
                    raise TokenExpiredError(
                        "The device code has expired. Please try again."
                    ) from exc
                if error in ("invalid_client", "unauthorized_client"):
                    raise ClientConfigurationError(
                        self._client_error_message()
                    ) from exc
                raise DeviceFlowError(
                    f"Unexpected error from token endpoint: {error}"
                ) from exc
            except httpx2.HTTPError as exc:
                raise DeviceFlowError(f"Token request failed: {exc}") from exc
            except ValueError as exc:
                raise DeviceFlowError(
                    f"Token request failed: the answer was not JSON ({exc})."
                ) from exc

            self._device_pkce = None
            return self._parse_token_response(body)

        raise TokenExpiredError("Timed out waiting for user authorization.")

    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        try:
            body = self._oauth.refresh_token(
                self._env.token_url, refresh_token=refresh_token
            )
        except (OAuthError, OAuth2Error) as exc:
            if exc.error == "invalid_grant":
                raise RefreshRejectedError(
                    f"Token refresh was refused: {exc.description or exc.error}"
                ) from exc
            if exc.error in ("invalid_client", "unauthorized_client"):
                raise ClientConfigurationError(self._client_error_message()) from exc
            raise DeviceFlowError(f"Token refresh failed: {exc.error}") from exc
        except httpx2.HTTPError as exc:
            raise DeviceFlowError(f"Token refresh failed: {exc}") from exc
        except ValueError as exc:
            raise DeviceFlowError(
                f"Token refresh failed: the answer was not JSON ({exc})."
            ) from exc

        tokens = self._parse_token_response(body)
        if not tokens.refresh_token:
            tokens.refresh_token = refresh_token
        return tokens

    def _client_error_message(self) -> str:
        return (
            f"Keycloak rejected OAuth client '{self._env.client_id}' in realm "
            f"'{self._env.realm}'. Check the client registration and device grant settings."
        )

    @staticmethod
    def _oauth_error_code(resp: httpx2.Response) -> str | None:
        try:
            body = resp.json()
        except ValueError:
            return None
        return body.get("error") if isinstance(body, dict) else None

    def get_userinfo(self, access_token: str) -> dict:
        try:
            resp = self._http.get(
                self._env.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except httpx2.HTTPError as exc:
            raise DeviceFlowError(f"Account request failed: {exc}") from exc
        self._raise_for_status(resp)
        return self._json(resp, "Account request")

    def revoke_token(self, token: str, token_type_hint: str = "refresh_token") -> None:
        """Revoke a token at Keycloak (RFC 7009), ending the session it belongs to.

        Raises DeviceFlowError when Keycloak cannot be reached or refuses, so
        the caller can warn; local tokens should be removed either way.
        """
        resp = self._post(
            self._env.revoke_url,
            {
                "client_id": self._env.client_id,
                "token": token,
                "token_type_hint": token_type_hint,
            },
            "Token revocation",
        )
        self._raise_for_status(resp)

    def _post(self, url: str, data: dict[str, str], what: str) -> httpx2.Response:
        """POST a form, turning a transport failure into a DeviceFlowError."""
        try:
            return self._http.post(url, data=data)
        except httpx2.HTTPError as exc:
            raise DeviceFlowError(f"{what} failed: {exc}") from exc

    @staticmethod
    def _json(resp: httpx2.Response, what: str) -> dict[str, Any]:
        """The response body as a JSON object, or a DeviceFlowError (a proxy's HTML error page, for example)."""
        try:
            body = resp.json()
        except ValueError as exc:
            raise DeviceFlowError(
                f"{what} failed: HTTP {resp.status_code} from {resp.url} was not JSON."
            ) from exc
        if not isinstance(body, dict):
            raise DeviceFlowError(f"{what} failed: unexpected answer from {resp.url}.")
        return body

    @staticmethod
    def _parse_token_response(body: dict[str, Any]) -> TokenResponse:
        return TokenResponse(
            access_token=body["access_token"],
            refresh_token=body.get("refresh_token"),
            id_token=body.get("id_token"),
            token_type=body.get("token_type", "Bearer"),
            expires_in=body.get("expires_in", 300),
            scope=body.get("scope"),
        )

    @staticmethod
    def _error_detail(resp: httpx2.Response) -> str:
        try:
            body = resp.json()
        except ValueError:
            return resp.text
        if isinstance(body, dict):
            return str(body.get("error_description") or body.get("error") or resp.text)
        return resp.text

    @staticmethod
    def _raise_for_status(resp: httpx2.Response) -> None:
        if resp.is_error:
            detail = KeycloakDeviceFlowClient._error_detail(resp)
            raise DeviceFlowError(f"HTTP {resp.status_code} from {resp.url}: {detail}")

    @staticmethod
    def to_stored_tokens(tr: TokenResponse) -> StoredTokens:
        from ce.config.settings import StoredTokens

        return StoredTokens(
            access_token=tr.access_token,
            refresh_token=tr.refresh_token,
            id_token=tr.id_token,
            token_type=tr.token_type,
            expires_at=time.time() + tr.expires_in,
            scope=tr.scope,
        )
