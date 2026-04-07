from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET, Unset
from ... import errors

from ...models.iir_api_submit_to_iir_response_200 import IIRApiSubmitToIIRResponse200
from ...models.issuer_dto import IssuerDTO


def _get_kwargs(
    *,
    body: IssuerDTO | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/iir/submitToIIR",
    }

    if body is not UNSET:
        _kwargs["json"] = body.to_dict()
        headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> IIRApiSubmitToIIRResponse200 | None:
    if response.status_code == 200:
        response_200 = IIRApiSubmitToIIRResponse200.from_dict(response.json())
        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[IIRApiSubmitToIIRResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: IssuerDTO | Unset = UNSET,
) -> Response[IIRApiSubmitToIIRResponse200]:
    kwargs = _get_kwargs(body=body)

    response = client.get_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: IssuerDTO | Unset = UNSET,
) -> IIRApiSubmitToIIRResponse200 | None:
    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: IssuerDTO | Unset = UNSET,
) -> Response[IIRApiSubmitToIIRResponse200]:
    kwargs = _get_kwargs(body=body)

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: IssuerDTO | Unset = UNSET,
) -> IIRApiSubmitToIIRResponse200 | None:
    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed