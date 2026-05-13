from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.iir_api_get_issuers_by_user_response_200 import IIRApiGetIssuersByUserResponse200
from ...types import UNSET, Unset
from typing import cast
from uuid import UUID



def _get_kwargs(
    user_id: UUID,
    *,
    page: int | Unset = UNSET,
    page_size: int | Unset = UNSET,
    keyword: str | Unset = UNSET,
    task: str | Unset = UNSET,

) -> dict[str, Any]:
    

    

    params: dict[str, Any] = {}

    params["page"] = page

    params["pageSize"] = page_size

    params["keyword"] = keyword

    params["task"] = task


    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}


    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/iir-api/users/{user_id}/issuers".format(user_id=quote(str(user_id), safe=""),),
        "params": params,
    }


    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> IIRApiGetIssuersByUserResponse200 | None:
    if response.status_code == 200:
        response_200 = IIRApiGetIssuersByUserResponse200.from_dict(response.json())



        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[IIRApiGetIssuersByUserResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    user_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    page_size: int | Unset = UNSET,
    keyword: str | Unset = UNSET,
    task: str | Unset = UNSET,

) -> Response[IIRApiGetIssuersByUserResponse200]:
    """ 
    Args:
        user_id (UUID):
        page (int | Unset):
        page_size (int | Unset):
        keyword (str | Unset):
        task (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[IIRApiGetIssuersByUserResponse200]
     """


    kwargs = _get_kwargs(
        user_id=user_id,
page=page,
page_size=page_size,
keyword=keyword,
task=task,

    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    user_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    page_size: int | Unset = UNSET,
    keyword: str | Unset = UNSET,
    task: str | Unset = UNSET,

) -> IIRApiGetIssuersByUserResponse200 | None:
    """ 
    Args:
        user_id (UUID):
        page (int | Unset):
        page_size (int | Unset):
        keyword (str | Unset):
        task (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        IIRApiGetIssuersByUserResponse200
     """


    return sync_detailed(
        user_id=user_id,
client=client,
page=page,
page_size=page_size,
keyword=keyword,
task=task,

    ).parsed

async def asyncio_detailed(
    user_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    page_size: int | Unset = UNSET,
    keyword: str | Unset = UNSET,
    task: str | Unset = UNSET,

) -> Response[IIRApiGetIssuersByUserResponse200]:
    """ 
    Args:
        user_id (UUID):
        page (int | Unset):
        page_size (int | Unset):
        keyword (str | Unset):
        task (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[IIRApiGetIssuersByUserResponse200]
     """


    kwargs = _get_kwargs(
        user_id=user_id,
page=page,
page_size=page_size,
keyword=keyword,
task=task,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    user_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    page: int | Unset = UNSET,
    page_size: int | Unset = UNSET,
    keyword: str | Unset = UNSET,
    task: str | Unset = UNSET,

) -> IIRApiGetIssuersByUserResponse200 | None:
    """ 
    Args:
        user_id (UUID):
        page (int | Unset):
        page_size (int | Unset):
        keyword (str | Unset):
        task (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        IIRApiGetIssuersByUserResponse200
     """


    return (await asyncio_detailed(
        user_id=user_id,
client=client,
page=page,
page_size=page_size,
keyword=keyword,
task=task,

    )).parsed
