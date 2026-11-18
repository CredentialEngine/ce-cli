from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define

from ..models.project_publish_status import ProjectPublishStatus
from ..models.project_status import ProjectStatus
from ..models.project_type import ProjectType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.iteration_summary_dto import IterationSummaryDto
    from ..models.project_reviewer_dto import ProjectReviewerDto
    from ..models.publishing_job_dto import PublishingJobDto


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
        iterations (list[IterationSummaryDto] | Unset):
        reviewers (list[ProjectReviewerDto] | Unset):
        publishing_jobs (list[PublishingJobDto] | Unset):
    """

    project_id: int
    name: str
    author_id: UUID
    status: ProjectStatus
    publish_status: ProjectPublishStatus
    project_type: ProjectType
    created_at: datetime.datetime
    updated_at: datetime.datetime
    iterations: list[IterationSummaryDto] | Unset = UNSET
    reviewers: list[ProjectReviewerDto] | Unset = UNSET
    publishing_jobs: list[PublishingJobDto] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        project_id = self.project_id

        name = self.name

        author_id = str(self.author_id)

        status = self.status.value

        publish_status = self.publish_status.value

        project_type = self.project_type.value

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        iterations: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.iterations, Unset):
            iterations = []
            for iterations_item_data in self.iterations:
                iterations_item = iterations_item_data.to_dict()
                iterations.append(iterations_item)

        reviewers: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.reviewers, Unset):
            reviewers = []
            for reviewers_item_data in self.reviewers:
                reviewers_item = reviewers_item_data.to_dict()
                reviewers.append(reviewers_item)

        publishing_jobs: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.publishing_jobs, Unset):
            publishing_jobs = []
            for publishing_jobs_item_data in self.publishing_jobs:
                publishing_jobs_item = publishing_jobs_item_data.to_dict()
                publishing_jobs.append(publishing_jobs_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "projectId": project_id,
                "name": name,
                "authorId": author_id,
                "status": status,
                "publishStatus": publish_status,
                "projectType": project_type,
                "createdAt": created_at,
                "updatedAt": updated_at,
            }
        )
        if iterations is not UNSET:
            field_dict["iterations"] = iterations
        if reviewers is not UNSET:
            field_dict["reviewers"] = reviewers
        if publishing_jobs is not UNSET:
            field_dict["publishingJobs"] = publishing_jobs

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.iteration_summary_dto import IterationSummaryDto  # noqa: PLC0415
        from ..models.project_reviewer_dto import ProjectReviewerDto  # noqa: PLC0415
        from ..models.publishing_job_dto import PublishingJobDto  # noqa: PLC0415

        d = dict(src_dict)
        project_id = d.pop("projectId")

        name = d.pop("name")

        author_id = UUID(d.pop("authorId"))

        status = ProjectStatus(d.pop("status"))

        publish_status = ProjectPublishStatus(d.pop("publishStatus"))

        project_type = ProjectType(d.pop("projectType"))

        created_at = datetime.datetime.fromisoformat(d.pop("createdAt"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updatedAt"))

        _iterations = d.pop("iterations", UNSET)
        iterations: list[IterationSummaryDto] | Unset = UNSET
        if _iterations is not UNSET:
            iterations = []
            for iterations_item_data in _iterations:
                iterations_item = IterationSummaryDto.from_dict(iterations_item_data)

                iterations.append(iterations_item)

        _reviewers = d.pop("reviewers", UNSET)
        reviewers: list[ProjectReviewerDto] | Unset = UNSET
        if _reviewers is not UNSET:
            reviewers = []
            for reviewers_item_data in _reviewers:
                reviewers_item = ProjectReviewerDto.from_dict(reviewers_item_data)

                reviewers.append(reviewers_item)

        _publishing_jobs = d.pop("publishingJobs", UNSET)
        publishing_jobs: list[PublishingJobDto] | Unset = UNSET
        if _publishing_jobs is not UNSET:
            publishing_jobs = []
            for publishing_jobs_item_data in _publishing_jobs:
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
