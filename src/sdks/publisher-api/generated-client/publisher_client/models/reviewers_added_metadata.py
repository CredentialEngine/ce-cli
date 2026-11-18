from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ReviewersAddedMetadata")


@_attrs_define
class ReviewersAddedMetadata:
    """
    Attributes:
        count (int | Unset):
        user_ids (list[UUID] | Unset):
    """

    count: int | Unset = UNSET
    user_ids: list[UUID] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        count = self.count

        user_ids: list[str] | Unset = UNSET
        if not isinstance(self.user_ids, Unset):
            user_ids = []
            for user_ids_item_data in self.user_ids:
                user_ids_item = str(user_ids_item_data)
                user_ids.append(user_ids_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if count is not UNSET:
            field_dict["count"] = count
        if user_ids is not UNSET:
            field_dict["userIds"] = user_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        count = d.pop("count", UNSET)

        _user_ids = d.pop("userIds", UNSET)
        user_ids: list[UUID] | Unset = UNSET
        if _user_ids is not UNSET:
            user_ids = []
            for user_ids_item_data in _user_ids:
                user_ids_item = UUID(user_ids_item_data)

                user_ids.append(user_ids_item)

        reviewers_added_metadata = cls(
            count=count,
            user_ids=user_ids,
        )

        return reviewers_added_metadata
