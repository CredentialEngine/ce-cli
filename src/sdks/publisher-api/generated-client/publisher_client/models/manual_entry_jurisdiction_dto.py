from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ManualEntryJurisdictionDto")


@_attrs_define
class ManualEntryJurisdictionDto:
    """
    Attributes:
        country (str):
        region (None | str | Unset):
    """

    country: str
    region: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        country = self.country

        region: None | str | Unset
        if isinstance(self.region, Unset):
            region = UNSET
        else:
            region = self.region

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "country": country,
            }
        )
        if region is not UNSET:
            field_dict["region"] = region

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        country = d.pop("country")

        def _parse_region(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        region = _parse_region(d.pop("region", UNSET))

        manual_entry_jurisdiction_dto = cls(
            country=country,
            region=region,
        )

        return manual_entry_jurisdiction_dto
