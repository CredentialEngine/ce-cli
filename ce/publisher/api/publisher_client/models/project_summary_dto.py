import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.project_publish_status import ProjectPublishStatus
from ..models.project_status import ProjectStatus
from ..models.project_type import ProjectType

T = TypeVar("T", bound="ProjectSummaryDto")


@_attrs_define
class ProjectSummaryDto:
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
    """

    project_id: int
    name: str
    author_id: UUID
    status: ProjectStatus
    publish_status: ProjectPublishStatus
    project_type: ProjectType
    created_at: datetime.datetime
    updated_at: datetime.datetime

    def to_dict(self) -> dict[str, Any]:
        project_id = self.project_id

        name = self.name

        author_id = str(self.author_id)

        status = self.status.value

        publish_status = self.publish_status.value

        project_type = self.project_type.value

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        project_id = d.pop("projectId")

        name = d.pop("name")

        author_id = UUID(d.pop("authorId"))

        status = ProjectStatus(d.pop("status"))

        publish_status = ProjectPublishStatus(d.pop("publishStatus"))

        project_type = ProjectType(d.pop("projectType"))

        created_at = isoparse(d.pop("createdAt"))

        updated_at = isoparse(d.pop("updatedAt"))

        project_summary_dto = cls(
            project_id=project_id,
            name=name,
            author_id=author_id,
            status=status,
            publish_status=publish_status,
            project_type=project_type,
            created_at=created_at,
            updated_at=updated_at,
        )

        return project_summary_dto
