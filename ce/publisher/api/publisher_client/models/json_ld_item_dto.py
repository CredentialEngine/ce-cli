from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="JsonLdItemDto")


@_attrs_define
class JsonLdItemDto:
    """
    Attributes:
        id (Union[None, Unset, str]):
        name (Union[None, Unset, str]):
        type_ (Union[None, Unset, str]):
        ctid (Union[None, Unset, str]):
        json_ld (Union[Unset, Any]):
    """

    id: Union[None, Unset, str] = UNSET
    name: Union[None, Unset, str] = UNSET
    type_: Union[None, Unset, str] = UNSET
    ctid: Union[None, Unset, str] = UNSET
    json_ld: Union[Unset, Any] = UNSET

    def to_dict(self) -> dict[str, Any]:
        id: Union[None, Unset, str]
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        name: Union[None, Unset, str]
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        type_: Union[None, Unset, str]
        if isinstance(self.type_, Unset):
            type_ = UNSET
        else:
            type_ = self.type_

        ctid: Union[None, Unset, str]
        if isinstance(self.ctid, Unset):
            ctid = UNSET
        else:
            ctid = self.ctid

        json_ld = self.json_ld

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if type_ is not UNSET:
            field_dict["type"] = type_
        if ctid is not UNSET:
            field_dict["ctid"] = ctid
        if json_ld is not UNSET:
            field_dict["jsonLd"] = json_ld

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_type_(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        type_ = _parse_type_(d.pop("type", UNSET))

        def _parse_ctid(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        ctid = _parse_ctid(d.pop("ctid", UNSET))

        json_ld = d.pop("jsonLd", UNSET)

        json_ld_item_dto = cls(
            id=id,
            name=name,
            type_=type_,
            ctid=ctid,
            json_ld=json_ld,
        )

        return json_ld_item_dto
