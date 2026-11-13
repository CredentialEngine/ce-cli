from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
  from ..models.validation_error_dto import ValidationErrorDto





T = TypeVar("T", bound="GetProjectsProjectIdIterationsIterationIdValidationResultsFileNameResponse200")



@_attrs_define
class GetProjectsProjectIdIterationsIterationIdValidationResultsFileNameResponse200:
    """ 
     """

    additional_properties: dict[str, list['ValidationErrorDto']] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        from ..models.validation_error_dto import ValidationErrorDto
        
        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            field_dict[prop_name] = []
            for additional_property_item_data in prop:
                additional_property_item = additional_property_item_data.to_dict()
                field_dict[prop_name].append(additional_property_item)




        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.validation_error_dto import ValidationErrorDto
        d = dict(src_dict)
        get_projects_project_id_iterations_iteration_id_validation_results_file_name_response_200 = cls(
        )


        additional_properties = {}
        for prop_name, prop_dict in d.items():
            additional_property = []
            _additional_property = prop_dict
            for additional_property_item_data in (_additional_property):
                additional_property_item = ValidationErrorDto.from_dict(additional_property_item_data)



                additional_property.append(additional_property_item)

            additional_properties[prop_name] = additional_property

        get_projects_project_id_iterations_iteration_id_validation_results_file_name_response_200.additional_properties = additional_properties
        return get_projects_project_id_iterations_iteration_id_validation_results_file_name_response_200

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> list['ValidationErrorDto']:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: list['ValidationErrorDto']) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
