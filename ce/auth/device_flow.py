"""Keycloak Device Authorization Grant flow"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

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

class KeycloakDeviceFlowClient:
    """Keycloak device authorization grant."""

    def __init__(self, env: "ce.config.context.Environment") -> None:
        self._env = env
        self._http = httpx.Client(
            timeout=30,
            verify=env.ssl_verify,
        )

    def request_device_code(self) -> DeviceAuthResponse:
        resp = self._http.post(
            self._env.device_auth_url,
            data={
                "client_id": self._env.client_id,
                "scope": self._env.scopes,
            },
        )
        self._raise_for_status(resp)
        body = resp.json()
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

        while time.monotonic() < deadline:
            time.sleep(poll_interval)
            resp = self._http.post(
                self._env.token_url,
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": device_code,
                    "client_id": self._env.client_id,
                },
            )
            body = resp.json()

            if resp.is_success:
                return TokenResponse(
                    access_token=body["access_token"],
                    refresh_token=body.get("refresh_token"),
                    id_token=body.get("id_token"),
                    token_type=body.get("token_type", "Bearer"),
                    expires_in=body.get("expires_in", 300),
                    scope=body.get("scope"),
                )

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
        resp = self._http.post(
            self._env.token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self._env.client_id,
            },
        )
        self._raise_for_status(resp)
        body = resp.json()
        return TokenResponse(
            access_token=body["access_token"],
            refresh_token=body.get("refresh_token", refresh_token),
            id_token=body.get("id_token"),
            token_type=body.get("token_type", "Bearer"),
            expires_in=body.get("expires_in", 300),
            scope=body.get("scope"),
        )

    def get_userinfo(self, access_token: str) -> dict:
        base = self._env.token_url.replace("/token", "")
        userinfo_url = f"{base}/userinfo"
        resp = self._http.get(
            userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self._raise_for_status(resp)
        return resp.json()

    def revoke_token(self, token: str, token_type_hint: str = "refresh_token") -> None:
        logout_url = self._env.token_url.replace("/token", "/logout")
        self._http.post(
            logout_url,
            data={
                "client_id": self._env.client_id,
                "token": token,
                "token_type_hint": token_type_hint,
            },
        )

    @staticmethod
    def _raise_for_status(resp: httpx.Response) -> None:
        if resp.is_error:
            try:
                detail = resp.json().get("error_description") or resp.text
            except Exception:
                detail = resp.text
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