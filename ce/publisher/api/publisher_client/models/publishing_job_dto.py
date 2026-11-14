import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.publishing_stage import PublishingStage
from ..types import UNSET, Unset

T = TypeVar("T", bound="PublishingJobDto")


@_attrs_define
class PublishingJobDto:
    """
    Attributes:
        job_id (UUID):
        iteration_id (int):
        stage (PublishingStage):
        status (str):
        updated_at (datetime.datetime):
        workflow_name (Union[None, Unset, str]):
        error_message (Union[None, Unset, str]):
    """

    job_id: UUID
    iteration_id: int
    stage: PublishingStage
    status: str
    updated_at: datetime.datetime
    workflow_name: Union[None, Unset, str] = UNSET
    error_message: Union[None, Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        job_id = str(self.job_id)

        iteration_id = self.iteration_id

        stage = self.stage.value

        status = self.status

        updated_at = self.updated_at.isoformat()

        workflow_name: Union[None, Unset, str]
        if isinstance(self.workflow_name, Unset):
            workflow_name = UNSET
        else:
            workflow_name = self.workflow_name

        error_message: Union[None, Unset, str]
        if isinstance(self.error_message, Unset):
            error_message = UNSET
        else:
            error_message = self.error_message

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "jobId": job_id,
                "iterationId": iteration_id,
                "stage": stage,
                "status": status,
                "updatedAt": updated_at,
            }
        )
        if workflow_name is not UNSET:
            field_dict["workflowName"] = workflow_name
        if error_message is not UNSET:
            field_dict["errorMessage"] = error_message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        job_id = UUID(d.pop("jobId"))

        iteration_id = d.pop("iterationId")

        stage = PublishingStage(d.pop("stage"))

        status = d.pop("status")

        updated_at = isoparse(d.pop("updatedAt"))

        def _parse_workflow_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        workflow_name = _parse_workflow_name(d.pop("workflowName", UNSET))

        def _parse_error_message(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        error_message = _parse_error_message(d.pop("errorMessage", UNSET))

        publishing_job_dto = cls(
            job_id=job_id,
            iteration_id=iteration_id,
            stage=stage,
            status=status,
            updated_at=updated_at,
            workflow_name=workflow_name,
            error_message=error_message,
        )

        return publishing_job_dto
