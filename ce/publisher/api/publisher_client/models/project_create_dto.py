from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..models.project_type import ProjectType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProjectCreateDto")


@_attrs_define
class ProjectCreateDto:
    """
    Attributes:
        name (str):
        project_type (Union[Unset, ProjectType]):
    """

    name: str
    project_type: Union[Unset, ProjectType] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        project_type: Union[Unset, str] = UNSET
        if not isinstance(self.project_type, Unset):
            project_type = self.project_type.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
            }
        )
        if project_type is not UNSET:
            field_dict["projectType"] = project_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        _project_type = d.pop("projectType", UNSET)
        project_type: Union[Unset, ProjectType]
        if isinstance(_project_type, Unset):
            project_type = UNSET
        else:
            project_type = ProjectType(_project_type)

        project_create_dto = cls(
            name=name,
            project_type=project_type,
        )

        return project_create_dto
