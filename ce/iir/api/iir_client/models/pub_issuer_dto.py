from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PubIssuerDTO")


@_attrs_define
class PubIssuerDTO:
    """
    Attributes:
        ctid (str | Unset):
        did (str | Unset):
        name (str | Unset):
        legal_name (str | Unset):
        credential_registry_uri (str | Unset):
        subject_web_page (str | Unset):
        logo_base_64 (str | Unset):
        logo_uri (str | Unset):
        valid_from (datetime.datetime | Unset):
        valid_until (datetime.datetime | Unset):
    """

    ctid: str | Unset = UNSET
    did: str | Unset = UNSET
    name: str | Unset = UNSET
    legal_name: str | Unset = UNSET
    credential_registry_uri: str | Unset = UNSET
    subject_web_page: str | Unset = UNSET
    logo_base_64: str | Unset = UNSET
    logo_uri: str | Unset = UNSET
    valid_from: datetime.datetime | Unset = UNSET
    valid_until: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ctid = self.ctid

        did = self.did

        name = self.name

        legal_name = self.legal_name

        credential_registry_uri = self.credential_registry_uri

        subject_web_page = self.subject_web_page

        logo_base_64 = self.logo_base_64

        logo_uri = self.logo_uri

        valid_from: str | Unset = UNSET
        if not isinstance(self.valid_from, Unset):
            valid_from = self.valid_from.isoformat()

        valid_until: str | Unset = UNSET
        if not isinstance(self.valid_until, Unset):
            valid_until = self.valid_until.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if ctid is not UNSET:
            field_dict["CTID"] = ctid
        if did is not UNSET:
            field_dict["DID"] = did
        if name is not UNSET:
            field_dict["Name"] = name
        if legal_name is not UNSET:
            field_dict["LegalName"] = legal_name
        if credential_registry_uri is not UNSET:
            field_dict["CredentialRegistryUri"] = credential_registry_uri
        if subject_web_page is not UNSET:
            field_dict["SubjectWebPage"] = subject_web_page
        if logo_base_64 is not UNSET:
            field_dict["LogoBase64"] = logo_base_64
        if logo_uri is not UNSET:
            field_dict["LogoUri"] = logo_uri
        if valid_from is not UNSET:
            field_dict["ValidFrom"] = valid_from
        if valid_until is not UNSET:
            field_dict["ValidUntil"] = valid_until

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        ctid = d.pop("CTID", UNSET)

        did = d.pop("DID", UNSET)

        name = d.pop("Name", UNSET)

        legal_name = d.pop("LegalName", UNSET)

        credential_registry_uri = d.pop("CredentialRegistryUri", UNSET)

        subject_web_page = d.pop("SubjectWebPage", UNSET)

        logo_base_64 = d.pop("LogoBase64", UNSET)

        logo_uri = d.pop("LogoUri", UNSET)

        _valid_from = d.pop("ValidFrom", UNSET)
        valid_from: datetime.datetime | Unset
        if isinstance(_valid_from, Unset):
            valid_from = UNSET
        else:
            valid_from = datetime.datetime.fromisoformat(_valid_from)

        _valid_until = d.pop("ValidUntil", UNSET)
        valid_until: datetime.datetime | Unset
        if isinstance(_valid_until, Unset):
            valid_until = UNSET
        else:
            valid_until = datetime.datetime.fromisoformat(_valid_until)

        pub_issuer_dto = cls(
            ctid=ctid,
            did=did,
            name=name,
            legal_name=legal_name,
            credential_registry_uri=credential_registry_uri,
            subject_web_page=subject_web_page,
            logo_base_64=logo_base_64,
            logo_uri=logo_uri,
            valid_from=valid_from,
            valid_until=valid_until,
        )

        pub_issuer_dto.additional_properties = d
        return pub_issuer_dto

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
