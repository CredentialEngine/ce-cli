from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ValidateJwtRequest")


@_attrs_define
class ValidateJwtRequest:
    """
    Attributes:
        jwt (str | Unset):
        challenge_id (UUID | Unset):  Example: 00000000-0000-0000-0000-000000000000.
    """

    jwt: str | Unset = UNSET
    challenge_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        jwt = self.jwt

        challenge_id: str | Unset = UNSET
        if not isinstance(self.challenge_id, Unset):
            challenge_id = str(self.challenge_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if jwt is not UNSET:
            field_dict["Jwt"] = jwt
        if challenge_id is not UNSET:
            field_dict["ChallengeId"] = challenge_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        jwt = d.pop("Jwt", UNSET)

        _challenge_id = d.pop("ChallengeId", UNSET)
        challenge_id: UUID | Unset
        if isinstance(_challenge_id, Unset):
            challenge_id = UNSET
        else:
            challenge_id = UUID(_challenge_id)

        validate_jwt_request = cls(
            jwt=jwt,
            challenge_id=challenge_id,
        )

        validate_jwt_request.additional_properties = d
        return validate_jwt_request

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
