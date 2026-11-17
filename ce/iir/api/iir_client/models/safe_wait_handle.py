from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SafeWaitHandle")


@_attrs_define
class SafeWaitHandle:
    """
    Attributes:
        is_invalid (bool | Unset):
        is_closed (bool | Unset):
    """

    is_invalid: bool | Unset = UNSET
    is_closed: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_invalid = self.is_invalid

        is_closed = self.is_closed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if is_invalid is not UNSET:
            field_dict["IsInvalid"] = is_invalid
        if is_closed is not UNSET:
            field_dict["IsClosed"] = is_closed

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_invalid = d.pop("IsInvalid", UNSET)

        is_closed = d.pop("IsClosed", UNSET)

        safe_wait_handle = cls(
            is_invalid=is_invalid,
            is_closed=is_closed,
        )

        safe_wait_handle.additional_properties = d
        return safe_wait_handle

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
