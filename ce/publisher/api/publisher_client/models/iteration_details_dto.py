import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..models.iteration_status import IterationStatus

T = TypeVar("T", bound="IterationDetailsDto")


@_attrs_define
class IterationDetailsDto:
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

        field_dict.update(
            {
                "iterationId": iteration_id,
                "authorId": author_id,
                "createdAt": created_at,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        iteration_id = d.pop("iterationId")

        author_id = UUID(d.pop("authorId"))

        created_at = isoparse(d.pop("createdAt"))

        status = IterationStatus(d.pop("status"))

        iteration_details_dto = cls(
            iteration_id=iteration_id,
            author_id=author_id,
            created_at=created_at,
            status=status,
        )

        return iteration_details_dto
