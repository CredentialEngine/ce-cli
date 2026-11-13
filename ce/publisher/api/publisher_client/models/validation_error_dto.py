from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.validation_error_type import ValidationErrorType






T = TypeVar("T", bound="ValidationErrorDto")



@_attrs_define
class ValidationErrorDto:
    """ 
        Attributes:
            row (int):
            column (str):
            value (str):
            message (str):
            type_ (ValidationErrorType):
     """

    row: int
    column: str
    value: str
    message: str
    type_: ValidationErrorType





    def to_dict(self) -> dict[str, Any]:
        row = self.row

        column = self.column

        value = self.value

        message = self.message

        type_ = self.type_.value


        field_dict: dict[str, Any] = {}

        field_dict.update({
            "row": row,
            "column": column,
            "value": value,
            "message": message,
            "type": type_,
        })

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        row = d.pop("row")

        column = d.pop("column")

        value = d.pop("value")

        message = d.pop("message")

        type_ = ValidationErrorType(d.pop("type"))




        validation_error_dto = cls(
            row=row,
            column=column,
            value=value,
            message=message,
            type_=type_,
        )

        return validation_error_dto

