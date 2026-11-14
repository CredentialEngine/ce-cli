from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.iteration_details_dto import IterationDetailsDto
from ...models.upload_json_ld_to_project_body import UploadJsonLdToProjectBody
from ...types import Response


def _get_kwargs(
    project_id: int,
    *,
    body: UploadJsonLdToProjectBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/projects/{project_id}/iterations/upload-jsonld",
    }

    _kwargs["files"] = body.to_multipart()

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[IterationDetailsDto, str]]:
    if response.status_code == 200:
        response_200 = IterationDetailsDto.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = cast(str, response.json())
        return response_400

    if response.status_code == 403:
        response_403 = cast(str, response.json())
        return response_403

    if response.status_code == 404:
        response_404 = cast(str, response.json())
        return response_404

    if response.status_code == 409:
        response_409 = cast(str, response.json())
        return response_409

    if response.status_code == 413:
        response_413 = cast(str, response.json())
        return response_413

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[IterationDetailsDto, str]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    project_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UploadJsonLdToProjectBody,
) -> Response[Union[IterationDetailsDto, str]]:
    """
    Args:
        project_id (int):
        body (UploadJsonLdToProjectBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[IterationDetailsDto, str]]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    project_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UploadJsonLdToProjectBody,
) -> Optional[Union[IterationDetailsDto, str]]:
    """
    Args:
        project_id (int):
        body (UploadJsonLdToProjectBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[IterationDetailsDto, str]
    """

    return sync_detailed(
        project_id=project_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    project_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UploadJsonLdToProjectBody,
) -> Response[Union[IterationDetailsDto, str]]:
    """
    Args:
        project_id (int):
        body (UploadJsonLdToProjectBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[IterationDetailsDto, str]]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    project_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    body: UploadJsonLdToProjectBody,
) -> Optional[Union[IterationDetailsDto, str]]:
    """
    Args:
        project_id (int):
        body (UploadJsonLdToProjectBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[IterationDetailsDto, str]
    """

    return (
        await asyncio_detailed(
            project_id=project_id,
            client=client,
            body=body,
        )
    ).parsed
