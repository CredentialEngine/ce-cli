from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="ProjectCreatedDto")


@_attrs_define
class ProjectCreatedDto:
    """
    Attributes:
        project_id (int):
    """

    project_id: int

    def to_dict(self) -> dict[str, Any]:
        project_id = self.project_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "projectId": project_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        project_id = d.pop("projectId")

        project_created_dto = cls(
            project_id=project_id,
        )

        return project_created_dto
