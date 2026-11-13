from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.project_publish_status import ProjectPublishStatus
from ..models.project_status import ProjectStatus
from ..models.project_type import ProjectType
from ..types import UNSET, Unset
from dateutil.parser import isoparse
from typing import cast
from typing import Union
from uuid import UUID
import datetime

if TYPE_CHECKING:
  from ..models.publishing_job_dto import PublishingJobDto
  from ..models.project_reviewer_dto import ProjectReviewerDto
  from ..models.iteration_summary_dto import IterationSummaryDto





T = TypeVar("T", bound="ProjectDetailsDto")



@_attrs_define
class ProjectDetailsDto:
    """ 
        Attributes:
            project_id (int):
            name (str):
            author_id (UUID):
            status (ProjectStatus):
            publish_status (ProjectPublishStatus):
            project_type (ProjectType):
            created_at (datetime.datetime):
            updated_at (datetime.datetime):
            iterations (Union[Unset, list['IterationSummaryDto']]):
            reviewers (Union[Unset, list['ProjectReviewerDto']]):
            publishing_jobs (Union[Unset, list['PublishingJobDto']]):
     """

    project_id: int
    name: str
    author_id: UUID
    status: ProjectStatus
    publish_status: ProjectPublishStatus
    project_type: ProjectType
    created_at: datetime.datetime
    updated_at: datetime.datetime
    iterations: Union[Unset, list['IterationSummaryDto']] = UNSET
    reviewers: Union[Unset, list['ProjectReviewerDto']] = UNSET
    publishing_jobs: Union[Unset, list['PublishingJobDto']] = UNSET





    def to_dict(self) -> dict[str, Any]:
        from ..models.publishing_job_dto import PublishingJobDto
        from ..models.project_reviewer_dto import ProjectReviewerDto
        from ..models.iteration_summary_dto import IterationSummaryDto
        project_id = self.project_id

        name = self.name

        author_id = str(self.author_id)

        status = self.status.value

        publish_status = self.publish_status.value

        project_type = self.project_type.value

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        iterations: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.iterations, Unset):
            iterations = []
            for iterations_item_data in self.iterations:
                iterations_item = iterations_item_data.to_dict()
                iterations.append(iterations_item)



        reviewers: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.reviewers, Unset):
            reviewers = []
            for reviewers_item_data in self.reviewers:
                reviewers_item = reviewers_item_data.to_dict()
                reviewers.append(reviewers_item)



        publishing_jobs: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.publishing_jobs, Unset):
            publishing_jobs = []
            for publishing_jobs_item_data in self.publishing_jobs:
                publishing_jobs_item = publishing_jobs_item_data.to_dict()
                publishing_jobs.append(publishing_jobs_item)




        field_dict: dict[str, Any] = {}

        field_dict.update({
            "projectId": project_id,
            "name": name,
            "authorId": author_id,
            "status": status,
            "publishStatus": publish_status,
            "projectType": project_type,
            "createdAt": created_at,
            "updatedAt": updated_at,
        })
        if iterations is not UNSET:
            field_dict["iterations"] = iterations
        if reviewers is not UNSET:
            field_dict["reviewers"] = reviewers
        if publishing_jobs is not UNSET:
            field_dict["publishingJobs"] = publishing_jobs

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.publishing_job_dto import PublishingJobDto
        from ..models.project_reviewer_dto import ProjectReviewerDto
        from ..models.iteration_summary_dto import IterationSummaryDto
        d = dict(src_dict)
        project_id = d.pop("projectId")

        name = d.pop("name")

        author_id = UUID(d.pop("authorId"))




        status = ProjectStatus(d.pop("status"))




        publish_status = ProjectPublishStatus(d.pop("publishStatus"))




        project_type = ProjectType(d.pop("projectType"))




        created_at = isoparse(d.pop("createdAt"))




        updated_at = isoparse(d.pop("updatedAt"))




        iterations = []
        _iterations = d.pop("iterations", UNSET)
        for iterations_item_data in (_iterations or []):
            iterations_item = IterationSummaryDto.from_dict(iterations_item_data)



            iterations.append(iterations_item)


        reviewers = []
        _reviewers = d.pop("reviewers", UNSET)
        for reviewers_item_data in (_reviewers or []):
            reviewers_item = ProjectReviewerDto.from_dict(reviewers_item_data)



            reviewers.append(reviewers_item)


        publishing_jobs = []
        _publishing_jobs = d.pop("publishingJobs", UNSET)
        for publishing_jobs_item_data in (_publishing_jobs or []):
            publishing_jobs_item = PublishingJobDto.from_dict(publishing_jobs_item_data)



            publishing_jobs.append(publishing_jobs_item)


        project_details_dto = cls(
            project_id=project_id,
            name=name,
            author_id=author_id,
            status=status,
            publish_status=publish_status,
            project_type=project_type,
            created_at=created_at,
            updated_at=updated_at,
            iterations=iterations,
            reviewers=reviewers,
            publishing_jobs=publishing_jobs,
        )

        return project_details_dto

