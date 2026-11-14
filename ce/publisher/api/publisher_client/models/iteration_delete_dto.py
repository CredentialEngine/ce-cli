from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

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

        field_dict.update(
            {
                "deleteFileNames": delete_file_names,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        delete_file_names = cast(list[str], d.pop("deleteFileNames"))

        iteration_delete_dto = cls(
            delete_file_names=delete_file_names,
        )

        return iteration_delete_dto
