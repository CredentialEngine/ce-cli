from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast, Union
from typing import Union






T = TypeVar("T", bound="JobResultDto")



@_attrs_define
class JobResultDto:
    """ 
        Attributes:
            job_type (str):
            success (Union[Unset, bool]):
            error_message (Union[None, Unset, str]):
     """

    job_type: str
    success: Union[Unset, bool] = UNSET
    error_message: Union[None, Unset, str] = UNSET





    def to_dict(self) -> dict[str, Any]:
        job_type = self.job_type

        success = self.success

        error_message: Union[None, Unset, str]
        if isinstance(self.error_message, Unset):
            error_message = UNSET
        else:
            error_message = self.error_message


        field_dict: dict[str, Any] = {}

        field_dict.update({
            "jobType": job_type,
        })
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

        def _parse_error_message(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        error_message = _parse_error_message(d.pop("errorMessage", UNSET))


        job_result_dto = cls(
            job_type=job_type,
            success=success,
            error_message=error_message,
        )

        return job_result_dto

