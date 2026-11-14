from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ManualEntryIdentifierDto")


@_attrs_define
class ManualEntryIdentifierDto:
    """
    Attributes:
        type_name (str):
        value_code (str):
        type_uri (Union[None, Unset, str]):
    """

    type_name: str
    value_code: str
    type_uri: Union[None, Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        type_name = self.type_name

        value_code = self.value_code

        type_uri: Union[None, Unset, str]
        if isinstance(self.type_uri, Unset):
            type_uri = UNSET
        else:
            type_uri = self.type_uri

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "typeName": type_name,
                "valueCode": value_code,
            }
        )
        if type_uri is not UNSET:
            field_dict["typeUri"] = type_uri

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_name = d.pop("typeName")

        value_code = d.pop("valueCode")

        def _parse_type_uri(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        type_uri = _parse_type_uri(d.pop("typeUri", UNSET))

        manual_entry_identifier_dto = cls(
            type_name=type_name,
            value_code=value_code,
            type_uri=type_uri,
        )

        return manual_entry_identifier_dto
