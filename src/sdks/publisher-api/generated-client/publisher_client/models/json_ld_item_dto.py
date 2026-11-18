from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="JsonLdItemDto")


@_attrs_define
class JsonLdItemDto:
    """
    Attributes:
        id (None | str | Unset):
        name (None | str | Unset):
        type_ (None | str | Unset):
        ctid (None | str | Unset):
        json_ld (Any | Unset):
    """

    id: None | str | Unset = UNSET
    name: None | str | Unset = UNSET
    type_: None | str | Unset = UNSET
    ctid: None | str | Unset = UNSET
    json_ld: Any | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        type_: None | str | Unset
        if isinstance(self.type_, Unset):
            type_ = UNSET
        else:
            type_ = self.type_

        ctid: None | str | Unset
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

        def _parse_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_type_(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        type_ = _parse_type_(d.pop("type", UNSET))

        def _parse_ctid(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

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
