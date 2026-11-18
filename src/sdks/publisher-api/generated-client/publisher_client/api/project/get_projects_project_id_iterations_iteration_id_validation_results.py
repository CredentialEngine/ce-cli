from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx2

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.i_action_result import IActionResult
from ...types import UNSET, Response, Unset


def _get_kwargs(
    project_id: int,
    iteration_id: int,
    *,
    limit_per_file: int | Unset = 5,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["limitPerFile"] = limit_per_file

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/projects/{project_id}/iterations/{iteration_id}/validationResults".format(
            project_id=quote(str(project_id), safe=""),
            iteration_id=quote(str(iteration_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx2.Response) -> IActionResult | None:
    if response.status_code == 200:
        response_200 = IActionResult.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx2.Response) -> Response[IActionResult]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    project_id: int,
    iteration_id: int,
    *,
    client: AuthenticatedClient | Client,
    limit_per_file: int | Unset = 5,
) -> Response[IActionResult]:
    """
    Args:
        project_id (int):
        iteration_id (int):
        limit_per_file (int | Unset):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx2.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[IActionResult]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        iteration_id=iteration_id,
        limit_per_file=limit_per_file,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    project_id: int,
    iteration_id: int,
    *,
    client: AuthenticatedClient | Client,
    limit_per_file: int | Unset = 5,
) -> IActionResult | None:
    """
    Args:
        project_id (int):
        iteration_id (int):
        limit_per_file (int | Unset):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx2.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        IActionResult
    """

    return sync_detailed(
        project_id=project_id,
        iteration_id=iteration_id,
        client=client,
        limit_per_file=limit_per_file,
    ).parsed


async def asyncio_detailed(
    project_id: int,
    iteration_id: int,
    *,
    client: AuthenticatedClient | Client,
    limit_per_file: int | Unset = 5,
) -> Response[IActionResult]:
    """
    Args:
        project_id (int):
        iteration_id (int):
        limit_per_file (int | Unset):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx2.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[IActionResult]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        iteration_id=iteration_id,
        limit_per_file=limit_per_file,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    project_id: int,
    iteration_id: int,
    *,
    client: AuthenticatedClient | Client,
    limit_per_file: int | Unset = 5,
) -> IActionResult | None:
    """
    Args:
        project_id (int):
        iteration_id (int):
        limit_per_file (int | Unset):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx2.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        IActionResult
    """

    return (
        await asyncio_detailed(
            project_id=project_id,
            iteration_id=iteration_id,
            client=client,
            limit_per_file=limit_per_file,
        )
    ).parsed
