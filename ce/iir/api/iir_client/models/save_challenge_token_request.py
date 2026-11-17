from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SaveChallengeTokenRequest")


@_attrs_define
class SaveChallengeTokenRequest:
    """
    Attributes:
        ctid (str | Unset):
        challenge_id (UUID | Unset):  Example: 00000000-0000-0000-0000-000000000000.
        token (str | Unset):
    """

    ctid: str | Unset = UNSET
    challenge_id: UUID | Unset = UNSET
    token: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ctid = self.ctid

        challenge_id: str | Unset = UNSET
        if not isinstance(self.challenge_id, Unset):
            challenge_id = str(self.challenge_id)

        token = self.token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if ctid is not UNSET:
            field_dict["Ctid"] = ctid
        if challenge_id is not UNSET:
            field_dict["ChallengeId"] = challenge_id
        if token is not UNSET:
            field_dict["Token"] = token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        ctid = d.pop("Ctid", UNSET)

        _challenge_id = d.pop("ChallengeId", UNSET)
        challenge_id: UUID | Unset
        if isinstance(_challenge_id, Unset):
            challenge_id = UNSET
        else:
            challenge_id = UUID(_challenge_id)

        token = d.pop("Token", UNSET)

        save_challenge_token_request = cls(
            ctid=ctid,
            challenge_id=challenge_id,
            token=token,
        )

        save_challenge_token_request.additional_properties = d
        return save_challenge_token_request

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
