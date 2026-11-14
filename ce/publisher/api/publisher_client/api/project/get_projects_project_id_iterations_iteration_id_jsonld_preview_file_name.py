from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.json_ld_item_dto import JsonLdItemDto
from ...types import Response


def _get_kwargs(
    project_id: int,
    iteration_id: int,
    file_name: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/projects/{project_id}/iterations/{iteration_id}/jsonld-preview/{file_name}",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[list["JsonLdItemDto"]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = JsonLdItemDto.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[list["JsonLdItemDto"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    project_id: int,
    iteration_id: int,
    file_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[list["JsonLdItemDto"]]:
    """
    Args:
        project_id (int):
        iteration_id (int):
        file_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['JsonLdItemDto']]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        iteration_id=iteration_id,
        file_name=file_name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    project_id: int,
    iteration_id: int,
    file_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[list["JsonLdItemDto"]]:
    """
    Args:
        project_id (int):
        iteration_id (int):
        file_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['JsonLdItemDto']
    """

    return sync_detailed(
        project_id=project_id,
        iteration_id=iteration_id,
        file_name=file_name,
        client=client,
    ).parsed


async def asyncio_detailed(
    project_id: int,
    iteration_id: int,
    file_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[list["JsonLdItemDto"]]:
    """
    Args:
        project_id (int):
        iteration_id (int):
        file_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['JsonLdItemDto']]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        iteration_id=iteration_id,
        file_name=file_name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    project_id: int,
    iteration_id: int,
    file_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[list["JsonLdItemDto"]]:
    """
    Args:
        project_id (int):
        iteration_id (int):
        file_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['JsonLdItemDto']
    """

    return (
        await asyncio_detailed(
            project_id=project_id,
            iteration_id=iteration_id,
            file_name=file_name,
            client=client,
        )
    ).parsed
