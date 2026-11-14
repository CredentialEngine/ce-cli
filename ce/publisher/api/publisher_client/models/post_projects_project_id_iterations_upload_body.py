import json
from collections.abc import Mapping
from io import BytesIO
from typing import TYPE_CHECKING, Any, TypeVar, Union

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
        files (Union[Unset, list[File]]):
        classifications (Union[Unset, list['IterationFileClassificationDto']]):
    """

    files: Union[Unset, list[File]] = UNSET
    classifications: Union[Unset, list["IterationFileClassificationDto"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        files: Union[Unset, list[FileTypes]] = UNSET
        if not isinstance(self.files, Unset):
            files = []
            for files_item_data in self.files:
                files_item = files_item_data.to_tuple()

                files.append(files_item)

        classifications: Union[Unset, list[dict[str, Any]]] = UNSET
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
        from ..models.iteration_file_classification_dto import IterationFileClassificationDto

        d = dict(src_dict)
        files = []
        _files = d.pop("Files", UNSET)
        for files_item_data in _files or []:
            files_item = File(payload=BytesIO(files_item_data))

            files.append(files_item)

        classifications = []
        _classifications = d.pop("Classifications", UNSET)
        for classifications_item_data in _classifications or []:
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
