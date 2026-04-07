from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
  from ..models.wait_handle import WaitHandle





T = TypeVar("T", bound="CancellationToken")



@_attrs_define
class CancellationToken:
    """ 
        Attributes:
            is_cancellation_requested (bool | Unset):
            can_be_canceled (bool | Unset):
            wait_handle (WaitHandle | Unset):
     """

    is_cancellation_requested: bool | Unset = UNSET
    can_be_canceled: bool | Unset = UNSET
    wait_handle: WaitHandle | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        from ..models.wait_handle import WaitHandle
        is_cancellation_requested = self.is_cancellation_requested

        can_be_canceled = self.can_be_canceled

        wait_handle: dict[str, Any] | Unset = UNSET
        if not isinstance(self.wait_handle, Unset):
            wait_handle = self.wait_handle.to_dict()


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if is_cancellation_requested is not UNSET:
            field_dict["IsCancellationRequested"] = is_cancellation_requested
        if can_be_canceled is not UNSET:
            field_dict["CanBeCanceled"] = can_be_canceled
        if wait_handle is not UNSET:
            field_dict["WaitHandle"] = wait_handle

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.wait_handle import WaitHandle
        d = dict(src_dict)
        is_cancellation_requested = d.pop("IsCancellationRequested", UNSET)

        can_be_canceled = d.pop("CanBeCanceled", UNSET)

        _wait_handle = d.pop("WaitHandle", UNSET)
        wait_handle: WaitHandle | Unset
        if isinstance(_wait_handle,  Unset):
            wait_handle = UNSET
        else:
            wait_handle = WaitHandle.from_dict(_wait_handle)




        cancellation_token = cls(
            is_cancellation_requested=is_cancellation_requested,
            can_be_canceled=can_be_canceled,
            wait_handle=wait_handle,
        )


        cancellation_token.additional_properties = d
        return cancellation_token

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
