from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset







T = TypeVar("T", bound="ManualEntryProjectCreatedDto")



@_attrs_define
class ManualEntryProjectCreatedDto:
    """ 
        Attributes:
            project_id (int):
            iteration_id (int):
     """

    project_id: int
    iteration_id: int





    def to_dict(self) -> dict[str, Any]:
        project_id = self.project_id

        iteration_id = self.iteration_id


        field_dict: dict[str, Any] = {}

        field_dict.update({
            "projectId": project_id,
            "iterationId": iteration_id,
        })

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        project_id = d.pop("projectId")

        iteration_id = d.pop("iterationId")

        manual_entry_project_created_dto = cls(
            project_id=project_id,
            iteration_id=iteration_id,
        )

        return manual_entry_project_created_dto

