from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx2

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET, Unset
from ... import errors

from ...models.iir_api_save_challenge_token_response_200 import IIRApiSaveChallengeTokenResponse200
from ...models.save_challenge_token_request import SaveChallengeTokenRequest
from typing import cast



def _get_kwargs(
    *,
    body:    SaveChallengeTokenRequest  |     SaveChallengeTokenRequest  | Unset = UNSET,

) -> dict[str, Any]:
    headers: dict[str, Any] = {}


    

    

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/iir-api/saveChallengeToken",
    }

    if isinstance(body, SaveChallengeTokenRequest):
        _kwargs["json"] = body.to_dict()


        headers["Content-Type"] = "application/json"
    if isinstance(body, SaveChallengeTokenRequest):
        _kwargs["data"] = body.to_dict()

        headers["Content-Type"] = "application/x-www-form-urlencoded"

    _kwargs["headers"] = headers
    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx2.Response) -> IIRApiSaveChallengeTokenResponse200 | None:
    if response.status_code == 200:
        response_200 = IIRApiSaveChallengeTokenResponse200.from_dict(response.json())



        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx2.Response) -> Response[IIRApiSaveChallengeTokenResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body:    SaveChallengeTokenRequest  |     SaveChallengeTokenRequest  | Unset = UNSET,

) -> Response[IIRApiSaveChallengeTokenResponse200]:
    """ 
    Args:
        body (SaveChallengeTokenRequest):
        body (SaveChallengeTokenRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx2.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[IIRApiSaveChallengeTokenResponse200]
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
    body:    SaveChallengeTokenRequest  |     SaveChallengeTokenRequest  | Unset = UNSET,

) -> IIRApiSaveChallengeTokenResponse200 | None:
    """ 
    Args:
        body (SaveChallengeTokenRequest):
        body (SaveChallengeTokenRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx2.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        IIRApiSaveChallengeTokenResponse200
     """


    return sync_detailed(
        client=client,
body=body,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body:    SaveChallengeTokenRequest  |     SaveChallengeTokenRequest  | Unset = UNSET,

) -> Response[IIRApiSaveChallengeTokenResponse200]:
    """ 
    Args:
        body (SaveChallengeTokenRequest):
        body (SaveChallengeTokenRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx2.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[IIRApiSaveChallengeTokenResponse200]
     """


    kwargs = _get_kwargs(
        body=body,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body:    SaveChallengeTokenRequest  |     SaveChallengeTokenRequest  | Unset = UNSET,

) -> IIRApiSaveChallengeTokenResponse200 | None:
    """ 
    Args:
        body (SaveChallengeTokenRequest):
        body (SaveChallengeTokenRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx2.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        IIRApiSaveChallengeTokenResponse200
     """


    return (await asyncio_detailed(
        client=client,
body=body,

    )).parsed
