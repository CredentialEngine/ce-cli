from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.iteration_status import IterationStatus
from dateutil.parser import isoparse
from typing import cast
from uuid import UUID
import datetime






T = TypeVar("T", bound="IterationSummaryDto")



@_attrs_define
class IterationSummaryDto:
    """ 
        Attributes:
            iteration_id (int):
            author_id (UUID):
            created_at (datetime.datetime):
            status (IterationStatus):
     """

    iteration_id: int
    author_id: UUID
    created_at: datetime.datetime
    status: IterationStatus





    def to_dict(self) -> dict[str, Any]:
        iteration_id = self.iteration_id

        author_id = str(self.author_id)

        created_at = self.created_at.isoformat()

        status = self.status.value


        field_dict: dict[str, Any] = {}

        field_dict.update({
            "iterationId": iteration_id,
            "authorId": author_id,
            "createdAt": created_at,
            "status": status,
        })

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        iteration_id = d.pop("iterationId")

        author_id = UUID(d.pop("authorId"))




        created_at = isoparse(d.pop("createdAt"))




        status = IterationStatus(d.pop("status"))




        iteration_summary_dto = cls(
            iteration_id=iteration_id,
            author_id=author_id,
            created_at=created_at,
            status=status,
        )

        return iteration_summary_dto

