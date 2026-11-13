"""Keycloak Device Authorization Grant flow"""

from __future__ import annotations

import base64
import hashlib
import secrets
import time
from dataclasses import dataclass
from typing import Any, Optional

import httpx


@dataclass
class DeviceAuthResponse:
    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: Optional[str]
    expires_in: int
    interval: int


@dataclass
class TokenResponse:
    access_token: str
    refresh_token: Optional[str]
    id_token: Optional[str]
    token_type: str
    expires_in: int
    scope: Optional[str]


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

class RefreshRejectedError(DeviceFlowError):
    """Keycloak refused the refresh token: the session ended or the token expired.

    Only signing in again helps. Other DeviceFlowErrors from a refresh (the
    server could not be reached, or answered with a server error) may pass.
    """


def create_pkce_pair() -> tuple[str, str]:
    """Return a new PKCE code verifier and its S256 challenge (RFC 7636)."""
    verifier = secrets.token_urlsafe(48)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


class KeycloakDeviceFlowClient:
    """Keycloak device authorization grant."""

    def __init__(
        self,
        env: "ce.config.context.Environment",
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self._env = env
        self._http = httpx.Client(
            timeout=30,
            verify=env.ssl_verify,
            transport=transport,
        )
        # The verifier of the device code being waited on, so a token can only
        # be collected by the process that started the sign-in.
        self._device_pkce: Optional[tuple[str, str]] = None

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
        on_pending: Optional[callable] = None,
    ) -> TokenResponse:
        deadline = time.monotonic() + expires_in
        poll_interval = interval

        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_code,
            "client_id": self._env.client_id,
        }
        if self._device_pkce is not None:
            pkce_device_code, verifier = self._device_pkce
            if pkce_device_code != device_code:
                raise DeviceFlowError("Device code does not match the pending PKCE session.")
            data["code_verifier"] = verifier

        while time.monotonic() < deadline:
            time.sleep(poll_interval)
            resp = self._post(self._env.token_url, data, "Token request")
            body = self._json(resp, "Token request")

            if resp.is_success:
                self._device_pkce = None
                return self._parse_token_response(body)

            error = body.get("error", "unknown_error")

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
                raise AccessDeniedError("Authorization was denied by the user.")
            if error in ("expired_token", "device_code_expired"):
                raise TokenExpiredError("The device code has expired. Please try again.")
            raise DeviceFlowError(f"Unexpected error from token endpoint: {error}")

        raise TokenExpiredError("Timed out waiting for user authorization.")

    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        resp = self._post(
            self._env.token_url,
            {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self._env.client_id,
            },
            "Token refresh",
        )

        if resp.status_code in (400, 401):
            # invalid_grant: the refresh token expired or the session was ended.
            raise RefreshRejectedError(f"Token refresh was refused: {self._error_detail(resp)}")

        self._raise_for_status(resp)
        body = self._json(resp, "Token refresh")
        tokens = self._parse_token_response(body)
        if tokens.refresh_token is None:
            tokens.refresh_token = refresh_token
        return tokens

    def get_userinfo(self, access_token: str) -> dict:
        base = self._env.token_url.replace("/token", "")
        userinfo_url = f"{base}/userinfo"
        try:
            resp = self._http.get(
                userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except httpx.HTTPError as exc:
            raise DeviceFlowError(f"Account request failed: {exc}") from exc
        self._raise_for_status(resp)
        return self._json(resp, "Account request")

    def revoke_token(self, token: str, token_type_hint: str = "refresh_token") -> None:
        """Revoke a token at Keycloak (RFC 7009), ending the session it belongs to.

        Raises DeviceFlowError when Keycloak cannot be reached or refuses, so
        the caller can warn; local tokens should be removed either way.
        """
        revoke_url = self._env.token_url.replace("/token", "/revoke")
        resp = self._post(
            revoke_url,
            {
                "client_id": self._env.client_id,
                "token": token,
                "token_type_hint": token_type_hint,
            },
            "Token revocation",
        )
        self._raise_for_status(resp)

    def _post(self, url: str, data: dict[str, str], what: str) -> httpx.Response:
        """POST a form, turning a transport failure into a DeviceFlowError."""
        try:
            return self._http.post(url, data=data)
        except httpx.HTTPError as exc:
            raise DeviceFlowError(f"{what} failed: {exc}") from exc

    @staticmethod
    def _json(resp: httpx.Response, what: str) -> dict[str, Any]:
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
    def _error_detail(resp: httpx.Response) -> str:
        try:
            body = resp.json()
        except ValueError:
            return resp.text
        if isinstance(body, dict):
            return str(body.get("error_description") or body.get("error") or resp.text)
        return resp.text

    @staticmethod
    def _raise_for_status(resp: httpx.Response) -> None:
        if resp.is_error:
            detail = KeycloakDeviceFlowClient._error_detail(resp)
            raise DeviceFlowError(f"HTTP {resp.status_code} from {resp.url}: {detail}")

    @staticmethod
    def to_stored_tokens(tr: TokenResponse) -> "ce.config.settings.StoredTokens":
        from ce.config.settings import StoredTokens
        return StoredTokens(
            access_token=tr.access_token,
            refresh_token=tr.refresh_token,
            id_token=tr.id_token,
            token_type=tr.token_type,
            expires_at=time.time() + tr.expires_in,
            scope=tr.scope,
        )
