from __future__ import annotations

import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Self

import httpx2

from ce.auth.token_manager import require_login
from ce.utils.logging import get_logger
from ce.utils.user_agent import USER_AGENT

log = get_logger(__name__)


class APIError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")


class CEHTTPClient:
    """Thin wrapper around httpx2.Client with auth, debug tracing, and error handling."""

    def __init__(self, base_url: str, access_token: str, timeout: float = 30.0) -> None:
        self._client = httpx2.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": USER_AGENT,
            },
            timeout=timeout,
        )
        self._base_url = base_url

    def get(self, path: str, **kwargs: Any) -> httpx2.Response:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx2.Response:
        return self._request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> httpx2.Response:
        return self._request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> httpx2.Response:
        return self._request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx2.Response:
        return self._request("DELETE", path, **kwargs)

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx2.Response:
        start = time.monotonic()
        log.debug("HTTP request: %s", method)
        resp = self._client.request(method, path, **kwargs)
        log.debug(
            "HTTP response: %s (%d ms)",
            resp.status_code,
            (time.monotonic() - start) * 1000,
        )
        self._raise_for_status(resp)
        return resp

    @staticmethod
    def _raise_for_status(resp: httpx2.Response) -> None:
        if resp.is_success:
            return
        try:
            body = resp.json()
            message = (
                body.get("message")
                or body.get("error_description")
                or body.get("error")
                or resp.text
            )
        except (ValueError, AttributeError, TypeError):
            message = resp.text or f"HTTP {resp.status_code}"
        raise APIError(resp.status_code, message)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


@contextmanager
def api_client(timeout: float = 30.0) -> Generator[CEHTTPClient, None, None]:
    """Context manager that yields an authenticated :class:`CEHTTPClient`.

    Automatically fetches (and refreshes) the access token and resolves
    the API base URL from the active environment.

    Raises:
        click.UsageError: if not logged in or no environment is configured.
    """
    access_token = require_login()
    from ce.config.context import require_environment

    _, _env = require_environment()
    base_url = _env.publisher_base.rstrip("/")
    log.debug("Authenticated HTTP client ready")
    client = CEHTTPClient(base_url, access_token, timeout=timeout)
    try:
        yield client
    finally:
        client.close()
