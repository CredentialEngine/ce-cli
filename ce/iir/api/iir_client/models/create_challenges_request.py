from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateChallengesRequest")


@_attrs_define
class CreateChallengesRequest:
    """
    Attributes:
        ctid (str | Unset):
        verification_method_ids (list[str] | Unset):
    """

    ctid: str | Unset = UNSET
    verification_method_ids: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ctid = self.ctid

        verification_method_ids: list[str] | Unset = UNSET
        if not isinstance(self.verification_method_ids, Unset):
            verification_method_ids = self.verification_method_ids

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if ctid is not UNSET:
            field_dict["Ctid"] = ctid
        if verification_method_ids is not UNSET:
            field_dict["VerificationMethodIds"] = verification_method_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        ctid = d.pop("Ctid", UNSET)

        verification_method_ids = cast(list[str], d.pop("VerificationMethodIds", UNSET))

        create_challenges_request = cls(
            ctid=ctid,
            verification_method_ids=verification_method_ids,
        )

        create_challenges_request.additional_properties = d
        return create_challenges_request

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
