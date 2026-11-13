from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field
import json
from .. import types

from ..types import UNSET, Unset

from ..types import File, FileTypes
from ..types import UNSET, Unset
from io import BytesIO
from typing import cast
from typing import Union






T = TypeVar("T", bound="UploadJsonLdToProjectBody")



@_attrs_define
class UploadJsonLdToProjectBody:
    """ 
        Attributes:
            files (Union[Unset, list[File]]):
     """

    files: Union[Unset, list[File]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        files: Union[Unset, list[FileTypes]] = UNSET
        if not isinstance(self.files, Unset):
            files = []
            for files_item_data in self.files:
                files_item = files_item_data.to_tuple()

                files.append(files_item)




        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if files is not UNSET:
            field_dict["Files"] = files

        return field_dict


    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        if not isinstance(self.files, Unset):
            for files_item_element in self.files:
                files.append(("Files", files_item_element.to_tuple()))





        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))



        return files


    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        files = []
        _files = d.pop("Files", UNSET)
        for files_item_data in (_files or []):
            files_item = File(
                 payload = BytesIO(files_item_data)
            )



            files.append(files_item)


        upload_json_ld_to_project_body = cls(
            files=files,
        )


        upload_json_ld_to_project_body.additional_properties = d
        return upload_json_ld_to_project_body

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
