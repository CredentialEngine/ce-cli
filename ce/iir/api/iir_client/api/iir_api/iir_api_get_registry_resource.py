from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.iir_api_get_registry_resource_response_200 import IIRApiGetRegistryResourceResponse200
from typing import cast



def _get_kwargs(
    *,
    ctid: str,

) -> dict[str, Any]:
    

    

    params: dict[str, Any] = {}

    params["ctid"] = ctid


    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}


    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/iir-api/getRegistryResource",
        "params": params,
    }


    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> IIRApiGetRegistryResourceResponse200 | None:
    if response.status_code == 200:
        response_200 = IIRApiGetRegistryResourceResponse200.from_dict(response.json())



        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[IIRApiGetRegistryResourceResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    ctid: str,

) -> Response[IIRApiGetRegistryResourceResponse200]:
    """ 
    Args:
        ctid (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[IIRApiGetRegistryResourceResponse200]
     """


    kwargs = _get_kwargs(
        ctid=ctid,

    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    *,
    client: AuthenticatedClient | Client,
    ctid: str,

) -> IIRApiGetRegistryResourceResponse200 | None:
    """ 
    Args:
        ctid (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        IIRApiGetRegistryResourceResponse200
     """


    return sync_detailed(
        client=client,
ctid=ctid,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    ctid: str,

) -> Response[IIRApiGetRegistryResourceResponse200]:
    """ 
    Args:
        ctid (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[IIRApiGetRegistryResourceResponse200]
     """


    kwargs = _get_kwargs(
        ctid=ctid,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    ctid: str,

) -> IIRApiGetRegistryResourceResponse200 | None:
    """ 
    Args:
        ctid (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        IIRApiGetRegistryResourceResponse200
     """


    return (await asyncio_detailed(
        client=client,
ctid=ctid,

    )).parsed
