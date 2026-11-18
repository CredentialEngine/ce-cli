from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="JobResultDto")


@_attrs_define
class JobResultDto:
    """
    Attributes:
        job_type (str):
        success (bool | Unset):
        error_message (None | str | Unset):
    """

    job_type: str
    success: bool | Unset = UNSET
    error_message: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        job_type = self.job_type

        success = self.success

        error_message: None | str | Unset
        if isinstance(self.error_message, Unset):
            error_message = UNSET
        else:
            error_message = self.error_message

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "jobType": job_type,
            }
        )
        if success is not UNSET:
            field_dict["success"] = success
        if error_message is not UNSET:
            field_dict["errorMessage"] = error_message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        job_type = d.pop("jobType")

        success = d.pop("success", UNSET)

        def _parse_error_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error_message = _parse_error_message(d.pop("errorMessage", UNSET))

        job_result_dto = cls(
            job_type=job_type,
            success=success,
            error_message=error_message,
        )

        return job_result_dto
