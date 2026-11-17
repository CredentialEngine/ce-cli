from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.safe_wait_handle import SafeWaitHandle
    from ..models.wait_handle_handle import WaitHandleHandle


T = TypeVar("T", bound="WaitHandle")


@_attrs_define
class WaitHandle:
    """
    Attributes:
        handle (WaitHandleHandle | Unset):
        safe_wait_handle (SafeWaitHandle | Unset):
    """

    handle: WaitHandleHandle | Unset = UNSET
    safe_wait_handle: SafeWaitHandle | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        handle: dict[str, Any] | Unset = UNSET
        if not isinstance(self.handle, Unset):
            handle = self.handle.to_dict()

        safe_wait_handle: dict[str, Any] | Unset = UNSET
        if not isinstance(self.safe_wait_handle, Unset):
            safe_wait_handle = self.safe_wait_handle.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if handle is not UNSET:
            field_dict["Handle"] = handle
        if safe_wait_handle is not UNSET:
            field_dict["SafeWaitHandle"] = safe_wait_handle

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.safe_wait_handle import SafeWaitHandle  # noqa: PLC0415
        from ..models.wait_handle_handle import WaitHandleHandle  # noqa: PLC0415

        d = dict(src_dict)
        _handle = d.pop("Handle", UNSET)
        handle: WaitHandleHandle | Unset
        if isinstance(_handle, Unset):
            handle = UNSET
        else:
            handle = WaitHandleHandle.from_dict(_handle)

        _safe_wait_handle = d.pop("SafeWaitHandle", UNSET)
        safe_wait_handle: SafeWaitHandle | Unset
        if isinstance(_safe_wait_handle, Unset):
            safe_wait_handle = UNSET
        else:
            safe_wait_handle = SafeWaitHandle.from_dict(_safe_wait_handle)

        wait_handle = cls(
            handle=handle,
            safe_wait_handle=safe_wait_handle,
        )

        wait_handle.additional_properties = d
        return wait_handle

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
