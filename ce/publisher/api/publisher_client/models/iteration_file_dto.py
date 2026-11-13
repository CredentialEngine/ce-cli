from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset







T = TypeVar("T", bound="IterationFileDto")



@_attrs_define
class IterationFileDto:
    """ 
        Attributes:
            file_name (str):
            resource_class (str):
     """

    file_name: str
    resource_class: str





    def to_dict(self) -> dict[str, Any]:
        file_name = self.file_name

        resource_class = self.resource_class


        field_dict: dict[str, Any] = {}

        field_dict.update({
            "fileName": file_name,
            "resourceClass": resource_class,
        })

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file_name = d.pop("fileName")

        resource_class = d.pop("resourceClass")

        iteration_file_dto = cls(
            file_name=file_name,
            resource_class=resource_class,
        )

        return iteration_file_dto

