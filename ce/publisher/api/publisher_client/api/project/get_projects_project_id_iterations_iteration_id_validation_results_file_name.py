from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.get_projects_project_id_iterations_iteration_id_validation_results_file_name_response_200 import GetProjectsProjectIdIterationsIterationIdValidationResultsFileNameResponse200
from ...types import UNSET, Unset
from typing import cast
from typing import Union



def _get_kwargs(
    project_id: int,
    iteration_id: int,
    file_name: str,
    *,
    limit_per_job: Union[Unset, int] = 50,

) -> dict[str, Any]:
    

    

    params: dict[str, Any] = {}

    params["limitPerJob"] = limit_per_job


    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}


    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/projects/{project_id}/iterations/{iteration_id}/validationResults/{file_name}".format(project_id=project_id,iteration_id=iteration_id,file_name=file_name,),
        "params": params,
    }


    return _kwargs



def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Optional[GetProjectsProjectIdIterationsIterationIdValidationResultsFileNameResponse200]:
    if response.status_code == 200:
        response_200 = GetProjectsProjectIdIterationsIterationIdValidationResultsFileNameResponse200.from_dict(response.json())



        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Response[GetProjectsProjectIdIterationsIterationIdValidationResultsFileNameResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    project_id: int,
    iteration_id: int,
    file_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    limit_per_job: Union[Unset, int] = 50,

) -> Response[GetProjectsProjectIdIterationsIterationIdValidationResultsFileNameResponse200]:
    """ 
    Args:
        project_id (int):
        iteration_id (int):
        file_name (str):
        limit_per_job (Union[Unset, int]):  Default: 50.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetProjectsProjectIdIterationsIterationIdValidationResultsFileNameResponse200]
     """


    kwargs = _get_kwargs(
        project_id=project_id,
iteration_id=iteration_id,
file_name=file_name,
limit_per_job=limit_per_job,

    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    project_id: int,
    iteration_id: int,
    file_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    limit_per_job: Union[Unset, int] = 50,

) -> Optional[GetProjectsProjectIdIterationsIterationIdValidationResultsFileNameResponse200]:
    """ 
    Args:
        project_id (int):
        iteration_id (int):
        file_name (str):
        limit_per_job (Union[Unset, int]):  Default: 50.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetProjectsProjectIdIterationsIterationIdValidationResultsFileNameResponse200
     """


    return sync_detailed(
        project_id=project_id,
iteration_id=iteration_id,
file_name=file_name,
client=client,
limit_per_job=limit_per_job,

    ).parsed

async def asyncio_detailed(
    project_id: int,
    iteration_id: int,
    file_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    limit_per_job: Union[Unset, int] = 50,

) -> Response[GetProjectsProjectIdIterationsIterationIdValidationResultsFileNameResponse200]:
    """ 
    Args:
        project_id (int):
        iteration_id (int):
        file_name (str):
        limit_per_job (Union[Unset, int]):  Default: 50.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetProjectsProjectIdIterationsIterationIdValidationResultsFileNameResponse200]
     """


    kwargs = _get_kwargs(
        project_id=project_id,
iteration_id=iteration_id,
file_name=file_name,
limit_per_job=limit_per_job,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    project_id: int,
    iteration_id: int,
    file_name: str,
    *,
    client: Union[AuthenticatedClient, Client],
    limit_per_job: Union[Unset, int] = 50,

) -> Optional[GetProjectsProjectIdIterationsIterationIdValidationResultsFileNameResponse200]:
    """ 
    Args:
        project_id (int):
        iteration_id (int):
        file_name (str):
        limit_per_job (Union[Unset, int]):  Default: 50.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetProjectsProjectIdIterationsIterationIdValidationResultsFileNameResponse200
     """


    return (await asyncio_detailed(
        project_id=project_id,
iteration_id=iteration_id,
file_name=file_name,
client=client,
limit_per_job=limit_per_job,

    )).parsed
