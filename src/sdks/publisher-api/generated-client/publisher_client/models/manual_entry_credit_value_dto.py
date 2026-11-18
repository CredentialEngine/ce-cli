from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ManualEntryCreditValueDto")


@_attrs_define
class ManualEntryCreditValueDto:
    """
    Attributes:
        credit_unit_type (None | str | Unset):
        exact_value (float | None | Unset):
        minimum_value (float | None | Unset):
        maximum_value (float | None | Unset):
        description (None | str | Unset):
    """

    credit_unit_type: None | str | Unset = UNSET
    exact_value: float | None | Unset = UNSET
    minimum_value: float | None | Unset = UNSET
    maximum_value: float | None | Unset = UNSET
    description: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        credit_unit_type: None | str | Unset
        if isinstance(self.credit_unit_type, Unset):
            credit_unit_type = UNSET
        else:
            credit_unit_type = self.credit_unit_type

        exact_value: float | None | Unset
        if isinstance(self.exact_value, Unset):
            exact_value = UNSET
        else:
            exact_value = self.exact_value

        minimum_value: float | None | Unset
        if isinstance(self.minimum_value, Unset):
            minimum_value = UNSET
        else:
            minimum_value = self.minimum_value

        maximum_value: float | None | Unset
        if isinstance(self.maximum_value, Unset):
            maximum_value = UNSET
        else:
            maximum_value = self.maximum_value

        description: None | str | Unset
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

        def _parse_credit_unit_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        credit_unit_type = _parse_credit_unit_type(d.pop("creditUnitType", UNSET))

        def _parse_exact_value(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        exact_value = _parse_exact_value(d.pop("exactValue", UNSET))

        def _parse_minimum_value(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        minimum_value = _parse_minimum_value(d.pop("minimumValue", UNSET))

        def _parse_maximum_value(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        maximum_value = _parse_maximum_value(d.pop("maximumValue", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        manual_entry_credit_value_dto = cls(
            credit_unit_type=credit_unit_type,
            exact_value=exact_value,
            minimum_value=minimum_value,
            maximum_value=maximum_value,
            description=description,
        )

        return manual_entry_credit_value_dto
