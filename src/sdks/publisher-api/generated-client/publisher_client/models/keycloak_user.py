from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.keycloak_user_attributes_type_0 import KeycloakUserAttributesType0


T = TypeVar("T", bound="KeycloakUser")


@_attrs_define
class KeycloakUser:
    """
    Attributes:
        id (UUID):
        email (str):
        first_name (str):
        last_name (str):
        full_name (str):
        organization (str):
        attributes (KeycloakUserAttributesType0 | None | Unset):
    """

    id: UUID
    email: str
    first_name: str
    last_name: str
    full_name: str
    organization: str
    attributes: KeycloakUserAttributesType0 | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.keycloak_user_attributes_type_0 import KeycloakUserAttributesType0  # noqa: PLC0415

        id = str(self.id)

        email = self.email

        first_name = self.first_name

        last_name = self.last_name

        full_name = self.full_name

        organization = self.organization

        attributes: dict[str, Any] | None | Unset
        if isinstance(self.attributes, Unset):
            attributes = UNSET
        elif isinstance(self.attributes, KeycloakUserAttributesType0):
            attributes = self.attributes.to_dict()
        else:
            attributes = self.attributes

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "email": email,
                "firstName": first_name,
                "lastName": last_name,
                "fullName": full_name,
                "organization": organization,
            }
        )
        if attributes is not UNSET:
            field_dict["attributes"] = attributes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.keycloak_user_attributes_type_0 import KeycloakUserAttributesType0  # noqa: PLC0415

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        email = d.pop("email")

        first_name = d.pop("firstName")

        last_name = d.pop("lastName")

        full_name = d.pop("fullName")

        organization = d.pop("organization")

        def _parse_attributes(data: object) -> KeycloakUserAttributesType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                attributes_type_0 = KeycloakUserAttributesType0.from_dict(data)

                return attributes_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(KeycloakUserAttributesType0 | None | Unset, data)

        attributes = _parse_attributes(d.pop("attributes", UNSET))

        keycloak_user = cls(
            id=id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            organization=organization,
            attributes=attributes,
        )

        return keycloak_user
