from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast, Union
from typing import Union






T = TypeVar("T", bound="ManualEntryJurisdictionDto")



@_attrs_define
class ManualEntryJurisdictionDto:
    """ 
        Attributes:
            country (str):
            region (Union[None, Unset, str]):
     """

    country: str
    region: Union[None, Unset, str] = UNSET





    def to_dict(self) -> dict[str, Any]:
        country = self.country

        region: Union[None, Unset, str]
        if isinstance(self.region, Unset):
            region = UNSET
        else:
            region = self.region


        field_dict: dict[str, Any] = {}

        field_dict.update({
            "country": country,
        })
        if region is not UNSET:
            field_dict["region"] = region

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        country = d.pop("country")

        def _parse_region(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        region = _parse_region(d.pop("region", UNSET))


        manual_entry_jurisdiction_dto = cls(
            country=country,
            region=region,
        )

        return manual_entry_jurisdiction_dto

