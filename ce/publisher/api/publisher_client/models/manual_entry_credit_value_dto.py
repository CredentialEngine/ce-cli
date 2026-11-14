from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ManualEntryCreditValueDto")


@_attrs_define
class ManualEntryCreditValueDto:
    """
    Attributes:
        credit_unit_type (Union[None, Unset, str]):
        exact_value (Union[None, Unset, float]):
        minimum_value (Union[None, Unset, float]):
        maximum_value (Union[None, Unset, float]):
        description (Union[None, Unset, str]):
    """

    credit_unit_type: Union[None, Unset, str] = UNSET
    exact_value: Union[None, Unset, float] = UNSET
    minimum_value: Union[None, Unset, float] = UNSET
    maximum_value: Union[None, Unset, float] = UNSET
    description: Union[None, Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        credit_unit_type: Union[None, Unset, str]
        if isinstance(self.credit_unit_type, Unset):
            credit_unit_type = UNSET
        else:
            credit_unit_type = self.credit_unit_type

        exact_value: Union[None, Unset, float]
        if isinstance(self.exact_value, Unset):
            exact_value = UNSET
        else:
            exact_value = self.exact_value

        minimum_value: Union[None, Unset, float]
        if isinstance(self.minimum_value, Unset):
            minimum_value = UNSET
        else:
            minimum_value = self.minimum_value

        maximum_value: Union[None, Unset, float]
        if isinstance(self.maximum_value, Unset):
            maximum_value = UNSET
        else:
            maximum_value = self.maximum_value

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if credit_unit_type is not UNSET:
            field_dict["creditUnitType"] = credit_unit_type
        if exact_value is not UNSET:
            field_dict["exactValue"] = exact_value
        if minimum_value is not UNSET:
            field_dict["minimumValue"] = minimum_value
        if maximum_value is not UNSET:
            field_dict["maximumValue"] = maximum_value
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_credit_unit_type(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        credit_unit_type = _parse_credit_unit_type(d.pop("creditUnitType", UNSET))

        def _parse_exact_value(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        exact_value = _parse_exact_value(d.pop("exactValue", UNSET))

        def _parse_minimum_value(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        minimum_value = _parse_minimum_value(d.pop("minimumValue", UNSET))

        def _parse_maximum_value(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        maximum_value = _parse_maximum_value(d.pop("maximumValue", UNSET))

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        manual_entry_credit_value_dto = cls(
            credit_unit_type=credit_unit_type,
            exact_value=exact_value,
            minimum_value=minimum_value,
            maximum_value=maximum_value,
            description=description,
        )

        return manual_entry_credit_value_dto
