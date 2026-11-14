from http import HTTPStatus
from io import BytesIO
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...types import File, Response


def _get_kwargs(
    project_id: int,
    iteration_id: int,
    file_name: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/projects/{project_id}/iterations/{iteration_id}/files/{file_name}",
    }

    return _kwargs


def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Optional[File]:
    if response.status_code == 200:
        response_200 = File(payload=BytesIO(response.json()))

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Response[File]:
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
) -> Response[File]:
    """
    Args:
        project_id (int):
        iteration_id (int):
        file_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[File]
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
) -> Optional[File]:
    """
    Args:
        project_id (int):
        iteration_id (int):
        file_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        File
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
) -> Response[File]:
    """
    Args:
        project_id (int):
        iteration_id (int):
        file_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[File]
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
) -> Optional[File]:
    """
    Args:
        project_id (int):
        iteration_id (int):
        file_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        File
    """

    return (
        await asyncio_detailed(
            project_id=project_id,
            iteration_id=iteration_id,
            file_name=file_name,
            client=client,
        )
    ).parsed
