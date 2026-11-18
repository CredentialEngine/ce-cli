from __future__ import annotations

import json
from collections.abc import Mapping
from io import BytesIO
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from .. import types
from ..types import UNSET, File, FileTypes, Unset

if TYPE_CHECKING:
    from ..models.iteration_file_classification_dto import IterationFileClassificationDto


T = TypeVar("T", bound="PostProjectsProjectIdIterationsUploadBody")


@_attrs_define
class PostProjectsProjectIdIterationsUploadBody:
    """
    Attributes:
        files (list[File] | Unset):
        classifications (list[IterationFileClassificationDto] | Unset):
    """

    files: list[File] | Unset = UNSET
    classifications: list[IterationFileClassificationDto] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        files: list[FileTypes] | Unset = UNSET
        if not isinstance(self.files, Unset):
            files = []
            for files_item_data in self.files:
                files_item = files_item_data.to_tuple()

                files.append(files_item)

        classifications: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.classifications, Unset):
            classifications = []
            for classifications_item_data in self.classifications:
                classifications_item = classifications_item_data.to_dict()
                classifications.append(classifications_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if files is not UNSET:
            field_dict["Files"] = files
        if classifications is not UNSET:
            field_dict["Classifications"] = classifications

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        if not isinstance(self.files, Unset):
            for files_item_element in self.files:
                files.append(("Files", files_item_element.to_tuple()))

        if not isinstance(self.classifications, Unset):
            for classifications_item_element in self.classifications:
                files.append(
                    (
                        "Classifications",
                        (None, json.dumps(classifications_item_element.to_dict()).encode(), "application/json"),
                    )
                )

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.iteration_file_classification_dto import IterationFileClassificationDto  # noqa: PLC0415

        d = dict(src_dict)
        _files = d.pop("Files", UNSET)
        files: list[File] | Unset = UNSET
        if _files is not UNSET:
            files = []
            for files_item_data in _files:
                files_item = File(payload=BytesIO(files_item_data))

                files.append(files_item)

        _classifications = d.pop("Classifications", UNSET)
        classifications: list[IterationFileClassificationDto] | Unset = UNSET
        if _classifications is not UNSET:
            classifications = []
            for classifications_item_data in _classifications:
                classifications_item = IterationFileClassificationDto.from_dict(classifications_item_data)

                classifications.append(classifications_item)

        post_projects_project_id_iterations_upload_body = cls(
            files=files,
            classifications=classifications,
        )

        post_projects_project_id_iterations_upload_body.additional_properties = d
        return post_projects_project_id_iterations_upload_body

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
