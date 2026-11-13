from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast, Union
from typing import Union






T = TypeVar("T", bound="ManualEntryDurationDto")



@_attrs_define
class ManualEntryDurationDto:
    """ 
        Attributes:
            exact_value (Union[None, Unset, float]):
            minimum_value (Union[None, Unset, float]):
            maximum_value (Union[None, Unset, float]):
            unit (Union[None, Unset, str]):
            description (Union[None, Unset, str]):
     """

    exact_value: Union[None, Unset, float] = UNSET
    minimum_value: Union[None, Unset, float] = UNSET
    maximum_value: Union[None, Unset, float] = UNSET
    unit: Union[None, Unset, str] = UNSET
    description: Union[None, Unset, str] = UNSET





    def to_dict(self) -> dict[str, Any]:
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

        unit: Union[None, Unset, str]
        if isinstance(self.unit, Unset):
            unit = UNSET
        else:
            unit = self.unit

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description


        field_dict: dict[str, Any] = {}

        field_dict.update({
        })
        if exact_value is not UNSET:
            field_dict["exactValue"] = exact_value
        if minimum_value is not UNSET:
            field_dict["minimumValue"] = minimum_value
        if maximum_value is not UNSET:
            field_dict["maximumValue"] = maximum_value
        if unit is not UNSET:
            field_dict["unit"] = unit
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
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


        def _parse_unit(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        unit = _parse_unit(d.pop("unit", UNSET))


        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))


        manual_entry_duration_dto = cls(
            exact_value=exact_value,
            minimum_value=minimum_value,
            maximum_value=maximum_value,
            unit=unit,
            description=description,
        )

        return manual_entry_duration_dto

