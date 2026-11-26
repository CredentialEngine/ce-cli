"""Shared authenticated Consumer API calls, independent of search and downloads."""

import asyncio
import logging

from consumer_api_client.exceptions import ApiException

from ce.auth.api_session import rejected_token, require_api_token

log = logging.getLogger(__name__)


class AuthenticatedApi:
    """Refresh and retry individual SDK calls, never an entire download command."""

    def __init__(self, api, config, env_name):
        self.api = api
        self.config = config
        self.env_name = env_name

    def __getattr__(self, name):
        method = getattr(self.api, name)

        async def call(*args, **kwargs):
            for refresh in (False, True):
                self.config.access_token = await asyncio.to_thread(
                    require_api_token, self.env_name, force_refresh=refresh
                )
                try:
                    log.debug("Consumer API operation: %s", name)
                    result = await method(*args, **kwargs)
                except ApiException as exc:
                    if exc.status != 401:
                        raise
                else:
                    if getattr(result, "status_code", None) != 401:
                        return result
                    await result.aclose()
                if refresh:
                    raise rejected_token()
                log.debug("Consumer API returned HTTP 401; refreshing token")
            raise AssertionError("unreachable")

        return call
