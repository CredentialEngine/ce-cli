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
    iteration_id: int,
    *,
    limit_per_file: Union[Unset, int] = 5,

) -> dict[str, Any]:
    

    

    params: dict[str, Any] = {}

    params["limitPerFile"] = limit_per_file


    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}


    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/projects/{project_id}/iterations/{iteration_id}/validationResults".format(project_id=project_id,iteration_id=iteration_id,),
        "params": params,
    }


    return _kwargs



def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Optional[IActionResult]:
    if response.status_code == 200:
        response_200 = IActionResult.from_dict(response.json())



        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Response[IActionResult]:
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
    client: Union[AuthenticatedClient, Client],
    limit_per_file: Union[Unset, int] = 5,

) -> Response[IActionResult]:
    """ 
    Args:
        project_id (int):
        iteration_id (int):
        limit_per_file (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

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
    client: Union[AuthenticatedClient, Client],
    limit_per_file: Union[Unset, int] = 5,

) -> Optional[IActionResult]:
    """ 
    Args:
        project_id (int):
        iteration_id (int):
        limit_per_file (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

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
    client: Union[AuthenticatedClient, Client],
    limit_per_file: Union[Unset, int] = 5,

) -> Response[IActionResult]:
    """ 
    Args:
        project_id (int):
        iteration_id (int):
        limit_per_file (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[IActionResult]
     """


    kwargs = _get_kwargs(
        project_id=project_id,
iteration_id=iteration_id,
limit_per_file=limit_per_file,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    project_id: int,
    iteration_id: int,
    *,
    client: Union[AuthenticatedClient, Client],
    limit_per_file: Union[Unset, int] = 5,

) -> Optional[IActionResult]:
    """ 
    Args:
        project_id (int):
        iteration_id (int):
        limit_per_file (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        IActionResult
     """


    return (await asyncio_detailed(
        project_id=project_id,
iteration_id=iteration_id,
client=client,
limit_per_file=limit_per_file,

    )).parsed
