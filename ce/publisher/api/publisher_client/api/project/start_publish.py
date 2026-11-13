from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.i_action_result import IActionResult
from ...types import UNSET, Unset
from typing import cast
from typing import Union



def _get_kwargs(
    project_id: int,
    *,
    iteration_id: Union[Unset, int] = UNSET,

) -> dict[str, Any]:
    

    

    params: dict[str, Any] = {}

    params["iterationId"] = iteration_id


    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}


    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/projects/{project_id}/publish/start".format(project_id=project_id,),
        "params": params,
    }


    return _kwargs



def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Optional[Union[IActionResult, str]]:
    if response.status_code == 200:
        response_200 = IActionResult.from_dict(response.json())



        return response_200

    if response.status_code == 403:
        response_403 = cast(str, response.json())
        return response_403

    if response.status_code == 404:
        response_404 = cast(str, response.json())
        return response_404

    if response.status_code == 409:
        response_409 = cast(str, response.json())
        return response_409

    if response.status_code == 503:
        response_503 = cast(str, response.json())
        return response_503

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Response[Union[IActionResult, str]]:
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
    iteration_id: Union[Unset, int] = UNSET,

) -> Response[Union[IActionResult, str]]:
    """ 
    Args:
        project_id (int):
        iteration_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[IActionResult, str]]
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
    *,
    client: Union[AuthenticatedClient, Client],
    iteration_id: Union[Unset, int] = UNSET,

) -> Optional[Union[IActionResult, str]]:
    """ 
    Args:
        project_id (int):
        iteration_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[IActionResult, str]
     """


    return sync_detailed(
        project_id=project_id,
client=client,
iteration_id=iteration_id,

    ).parsed

async def asyncio_detailed(
    project_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    iteration_id: Union[Unset, int] = UNSET,

) -> Response[Union[IActionResult, str]]:
    """ 
    Args:
        project_id (int):
        iteration_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[IActionResult, str]]
     """


    kwargs = _get_kwargs(
        project_id=project_id,
iteration_id=iteration_id,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    project_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    iteration_id: Union[Unset, int] = UNSET,

) -> Optional[Union[IActionResult, str]]:
    """ 
    Args:
        project_id (int):
        iteration_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[IActionResult, str]
     """


    return (await asyncio_detailed(
        project_id=project_id,
client=client,
iteration_id=iteration_id,

    )).parsed
