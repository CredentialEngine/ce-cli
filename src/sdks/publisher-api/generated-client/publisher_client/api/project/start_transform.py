from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx2

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.i_action_result import IActionResult
from ...types import Response


def _get_kwargs(
    project_id: int,
    iteration_id: int,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/projects/{project_id}/iterations/{iteration_id}/transform".format(
            project_id=quote(str(project_id), safe=""),
            iteration_id=quote(str(iteration_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx2.Response) -> IActionResult | str | None:
    if response.status_code == 200:
        response_200 = IActionResult.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = cast(str, response.json())
        return response_400

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx2.Response
) -> Response[IActionResult | str]:
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
) -> Response[IActionResult | str]:
    """
    Args:
        project_id (int):
        iteration_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx2.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[IActionResult | str]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        iteration_id=iteration_id,
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
) -> IActionResult | str | None:
    """
    Args:
        project_id (int):
        iteration_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx2.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        IActionResult | str
    """

    return sync_detailed(
        project_id=project_id,
        iteration_id=iteration_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    project_id: int,
    iteration_id: int,
    *,
    client: AuthenticatedClient | Client,
) -> Response[IActionResult | str]:
    """
    Args:
        project_id (int):
        iteration_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx2.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[IActionResult | str]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        iteration_id=iteration_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    project_id: int,
    iteration_id: int,
    *,
    client: AuthenticatedClient | Client,
) -> IActionResult | str | None:
    """
    Args:
        project_id (int):
        iteration_id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx2.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        IActionResult | str
    """

    return (
        await asyncio_detailed(
            project_id=project_id,
            iteration_id=iteration_id,
            client=client,
        )
    ).parsed
