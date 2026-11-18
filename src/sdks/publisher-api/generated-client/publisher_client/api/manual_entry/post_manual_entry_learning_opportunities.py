from http import HTTPStatus
from typing import Any

import httpx2

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_learning_opportunity_manual_entry_dto import CreateLearningOpportunityManualEntryDto
from ...models.manual_entry_project_created_dto import ManualEntryProjectCreatedDto
from ...models.problem_details import ProblemDetails
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: CreateLearningOpportunityManualEntryDto | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/manual-entry/learning-opportunities",
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx2.Response
) -> ManualEntryProjectCreatedDto | ProblemDetails | None:
    if response.status_code == 201:
        response_201 = ManualEntryProjectCreatedDto.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = ProblemDetails.from_dict(response.json())

        return response_400

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx2.Response
) -> Response[ManualEntryProjectCreatedDto | ProblemDetails]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateLearningOpportunityManualEntryDto | Unset = UNSET,
) -> Response[ManualEntryProjectCreatedDto | ProblemDetails]:
    """
    Args:
        body (CreateLearningOpportunityManualEntryDto | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx2.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManualEntryProjectCreatedDto | ProblemDetails]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: CreateLearningOpportunityManualEntryDto | Unset = UNSET,
) -> ManualEntryProjectCreatedDto | ProblemDetails | None:
    """
    Args:
        body (CreateLearningOpportunityManualEntryDto | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx2.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManualEntryProjectCreatedDto | ProblemDetails
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateLearningOpportunityManualEntryDto | Unset = UNSET,
) -> Response[ManualEntryProjectCreatedDto | ProblemDetails]:
    """
    Args:
        body (CreateLearningOpportunityManualEntryDto | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx2.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ManualEntryProjectCreatedDto | ProblemDetails]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateLearningOpportunityManualEntryDto | Unset = UNSET,
) -> ManualEntryProjectCreatedDto | ProblemDetails | None:
    """
    Args:
        body (CreateLearningOpportunityManualEntryDto | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx2.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ManualEntryProjectCreatedDto | ProblemDetails
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
