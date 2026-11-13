from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.problem_details import ProblemDetails
from ...models.template_dto import TemplateDto
from typing import cast



def _get_kwargs(
    route_name: str,

) -> dict[str, Any]:
    

    

    

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/templates/{route_name}".format(route_name=route_name,),
    }


    return _kwargs



def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Optional[Union[ProblemDetails, TemplateDto]]:
    if response.status_code == 200:
        response_200 = TemplateDto.from_dict(response.json())



        return response_200

    if response.status_code == 404:
        response_404 = ProblemDetails.from_dict(response.json())



        return response_404

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Response[Union[ProblemDetails, TemplateDto]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    route_name: str,
    *,
    client: Union[AuthenticatedClient, Client],

) -> Response[Union[ProblemDetails, TemplateDto]]:
    """ 
    Args:
        route_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ProblemDetails, TemplateDto]]
     """


    kwargs = _get_kwargs(
        route_name=route_name,

    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    route_name: str,
    *,
    client: Union[AuthenticatedClient, Client],

) -> Optional[Union[ProblemDetails, TemplateDto]]:
    """ 
    Args:
        route_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ProblemDetails, TemplateDto]
     """


    return sync_detailed(
        route_name=route_name,
client=client,

    ).parsed

async def asyncio_detailed(
    route_name: str,
    *,
    client: Union[AuthenticatedClient, Client],

) -> Response[Union[ProblemDetails, TemplateDto]]:
    """ 
    Args:
        route_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ProblemDetails, TemplateDto]]
     """


    kwargs = _get_kwargs(
        route_name=route_name,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    route_name: str,
    *,
    client: Union[AuthenticatedClient, Client],

) -> Optional[Union[ProblemDetails, TemplateDto]]:
    """ 
    Args:
        route_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ProblemDetails, TemplateDto]
     """


    return (await asyncio_detailed(
        route_name=route_name,
client=client,

    )).parsed
