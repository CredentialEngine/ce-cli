from collections.abc import Mapping
from typing import Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ReviewersRemovedMetadata")


@_attrs_define
class ReviewersRemovedMetadata:
    """
    Attributes:
        count (Union[Unset, int]):
        user_ids (Union[Unset, list[UUID]]):
    """

    count: Union[Unset, int] = UNSET
    user_ids: Union[Unset, list[UUID]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        count = self.count

        user_ids: Union[Unset, list[str]] = UNSET
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

        user_ids = []
        _user_ids = d.pop("userIds", UNSET)
        for user_ids_item_data in _user_ids or []:
            user_ids_item = UUID(user_ids_item_data)

            user_ids.append(user_ids_item)

        reviewers_removed_metadata = cls(
            count=count,
            user_ids=user_ids,
        )

        return reviewers_removed_metadata
