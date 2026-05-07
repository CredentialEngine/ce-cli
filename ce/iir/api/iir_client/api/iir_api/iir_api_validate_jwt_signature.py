from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET, Unset
from ... import errors

from ...models.iir_api_validate_jwt_signature_response_200 import IIRApiValidateJwtSignatureResponse200
from ...models.validate_jwt_request import ValidateJwtRequest
from typing import cast



def _get_kwargs(
    *,
    body:    ValidateJwtRequest  |     ValidateJwtRequest  | Unset = UNSET,

) -> dict[str, Any]:
    headers: dict[str, Any] = {}


    

    

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/iir-api/validateJwt",
    }

    if isinstance(body, ValidateJwtRequest):
        _kwargs["json"] = body.to_dict()


        headers["Content-Type"] = "application/json"
    if isinstance(body, ValidateJwtRequest):
        _kwargs["data"] = body.to_dict()

        headers["Content-Type"] = "application/x-www-form-urlencoded"

    _kwargs["headers"] = headers
    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> IIRApiValidateJwtSignatureResponse200 | None:
    if response.status_code == 200:
        response_200 = IIRApiValidateJwtSignatureResponse200.from_dict(response.json())



        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[IIRApiValidateJwtSignatureResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body:    ValidateJwtRequest  |     ValidateJwtRequest  | Unset = UNSET,

) -> Response[IIRApiValidateJwtSignatureResponse200]:
    """ 
    Args:
        body (ValidateJwtRequest):
        body (ValidateJwtRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[IIRApiValidateJwtSignatureResponse200]
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
    body:    ValidateJwtRequest  |     ValidateJwtRequest  | Unset = UNSET,

) -> IIRApiValidateJwtSignatureResponse200 | None:
    """ 
    Args:
        body (ValidateJwtRequest):
        body (ValidateJwtRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        IIRApiValidateJwtSignatureResponse200
     """


    return sync_detailed(
        client=client,
body=body,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body:    ValidateJwtRequest  |     ValidateJwtRequest  | Unset = UNSET,

) -> Response[IIRApiValidateJwtSignatureResponse200]:
    """ 
    Args:
        body (ValidateJwtRequest):
        body (ValidateJwtRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[IIRApiValidateJwtSignatureResponse200]
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
    body:    ValidateJwtRequest  |     ValidateJwtRequest  | Unset = UNSET,

) -> IIRApiValidateJwtSignatureResponse200 | None:
    """ 
    Args:
        body (ValidateJwtRequest):
        body (ValidateJwtRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        IIRApiValidateJwtSignatureResponse200
     """


    return (await asyncio_detailed(
        client=client,
body=body,

    )).parsed
