from http import HTTPStatus
from typing import Any

import httpx2

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.iir_api_validate_key_response_200 import IirApiValidateKeyResponse200
from ...types import UNSET, Response


def _get_kwargs(
    *,
    did: str,
    alg: str,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["did"] = did

    params["alg"] = alg

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/iir-api/validateDidKey",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx2.Response
) -> IirApiValidateKeyResponse200 | None:
    if response.status_code == 200:
        response_200 = IirApiValidateKeyResponse200.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx2.Response
) -> Response[IirApiValidateKeyResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    did: str,
    alg: str,
) -> Response[IirApiValidateKeyResponse200]:
    """
    Args:
        did (str):
        alg (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx2.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[IirApiValidateKeyResponse200]
    """

    kwargs = _get_kwargs(
        did=did,
        alg=alg,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    did: str,
    alg: str,
) -> IirApiValidateKeyResponse200 | None:
    """
    Args:
        did (str):
        alg (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx2.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        IirApiValidateKeyResponse200
    """

    return sync_detailed(
        client=client,
        did=did,
        alg=alg,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    did: str,
    alg: str,
) -> Response[IirApiValidateKeyResponse200]:
    """
    Args:
        did (str):
        alg (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx2.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[IirApiValidateKeyResponse200]
    """

    kwargs = _get_kwargs(
        did=did,
        alg=alg,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    did: str,
    alg: str,
) -> IirApiValidateKeyResponse200 | None:
    """
    Args:
        did (str):
        alg (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx2.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        IirApiValidateKeyResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            did=did,
            alg=alg,
        )
    ).parsed
