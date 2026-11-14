from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="IterationFilesAddedMetadata")


@_attrs_define
class IterationFilesAddedMetadata:
    """
    Attributes:
        iteration_id (Union[Unset, int]):
        count (Union[Unset, int]):
        file_names (Union[Unset, list[str]]):
    """

    iteration_id: Union[Unset, int] = UNSET
    count: Union[Unset, int] = UNSET
    file_names: Union[Unset, list[str]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        iteration_id = self.iteration_id

        count = self.count

        file_names: Union[Unset, list[str]] = UNSET
        if not isinstance(self.file_names, Unset):
            file_names = self.file_names

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if iteration_id is not UNSET:
            field_dict["iterationId"] = iteration_id
        if count is not UNSET:
            field_dict["count"] = count
        if file_names is not UNSET:
            field_dict["fileNames"] = file_names

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        iteration_id = d.pop("iterationId", UNSET)

        count = d.pop("count", UNSET)

        file_names = cast(list[str], d.pop("fileNames", UNSET))

        iteration_files_added_metadata = cls(
            iteration_id=iteration_id,
            count=count,
            file_names=file_names,
        )

        return iteration_files_added_metadata
