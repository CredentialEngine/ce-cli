from collections.abc import Mapping
from typing import Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="AddProjectReviewerDto")


@_attrs_define
class AddProjectReviewerDto:
    """
    Attributes:
        user_id (UUID):
        is_required (Union[Unset, bool]):
    """

    user_id: UUID
    is_required: Union[Unset, bool] = UNSET

    def to_dict(self) -> dict[str, Any]:
        user_id = str(self.user_id)

        is_required = self.is_required

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "userId": user_id,
            }
        )
        if is_required is not UNSET:
            field_dict["isRequired"] = is_required

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_id = UUID(d.pop("userId"))

        is_required = d.pop("isRequired", UNSET)

        add_project_reviewer_dto = cls(
            user_id=user_id,
            is_required=is_required,
        )

        return add_project_reviewer_dto
