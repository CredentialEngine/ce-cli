from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import Union
from uuid import UUID






T = TypeVar("T", bound="ProjectReviewerDto")



@_attrs_define
class ProjectReviewerDto:
    """ 
        Attributes:
            user_id (UUID):
            is_required (Union[Unset, bool]):
            is_approved (Union[Unset, bool]):
     """

    user_id: UUID
    is_required: Union[Unset, bool] = UNSET
    is_approved: Union[Unset, bool] = UNSET





    def to_dict(self) -> dict[str, Any]:
        user_id = str(self.user_id)

        is_required = self.is_required

        is_approved = self.is_approved


        field_dict: dict[str, Any] = {}

        field_dict.update({
            "userId": user_id,
        })
        if is_required is not UNSET:
            field_dict["isRequired"] = is_required
        if is_approved is not UNSET:
            field_dict["isApproved"] = is_approved

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_id = UUID(d.pop("userId"))




        is_required = d.pop("isRequired", UNSET)

        is_approved = d.pop("isApproved", UNSET)

        project_reviewer_dto = cls(
            user_id=user_id,
            is_required=is_required,
            is_approved=is_approved,
        )

        return project_reviewer_dto

