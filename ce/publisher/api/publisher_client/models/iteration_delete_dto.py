from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast






T = TypeVar("T", bound="IterationDeleteDto")



@_attrs_define
class IterationDeleteDto:
    """ 
        Attributes:
            delete_file_names (list[str]):
     """

    delete_file_names: list[str]





    def to_dict(self) -> dict[str, Any]:
        delete_file_names = self.delete_file_names




        field_dict: dict[str, Any] = {}

        field_dict.update({
            "deleteFileNames": delete_file_names,
        })

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        delete_file_names = cast(list[str], d.pop("deleteFileNames"))


        iteration_delete_dto = cls(
            delete_file_names=delete_file_names,
        )

        return iteration_delete_dto

