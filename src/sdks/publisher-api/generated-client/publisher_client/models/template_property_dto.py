from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="TemplatePropertyDto")


@_attrs_define
class TemplatePropertyDto:
    """
    Attributes:
        key (str | Unset):
        property_ (str | Unset):
        definition (str | Unset):
        specification (str | Unset):
        link (None | str | Unset):
        controlled_vocabulary (None | str | Unset):
        allowed_values (list[str] | Unset):
        multiple (bool | Unset):
        required (bool | Unset):
        sample (str | Unset):
        order (int | Unset):
    """

    key: str | Unset = UNSET
    property_: str | Unset = UNSET
    definition: str | Unset = UNSET
    specification: str | Unset = UNSET
    link: None | str | Unset = UNSET
    controlled_vocabulary: None | str | Unset = UNSET
    allowed_values: list[str] | Unset = UNSET
    multiple: bool | Unset = UNSET
    required: bool | Unset = UNSET
    sample: str | Unset = UNSET
    order: int | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        key = self.key

        property_ = self.property_

        definition = self.definition

        specification = self.specification

        link: None | str | Unset
        if isinstance(self.link, Unset):
            link = UNSET
        else:
            link = self.link

        controlled_vocabulary: None | str | Unset
        if isinstance(self.controlled_vocabulary, Unset):
            controlled_vocabulary = UNSET
        else:
            controlled_vocabulary = self.controlled_vocabulary

        allowed_values: list[str] | Unset = UNSET
        if not isinstance(self.allowed_values, Unset):
            allowed_values = self.allowed_values

        multiple = self.multiple

        required = self.required

        sample = self.sample

        order = self.order

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if key is not UNSET:
            field_dict["key"] = key
        if property_ is not UNSET:
            field_dict["property"] = property_
        if definition is not UNSET:
            field_dict["definition"] = definition
        if specification is not UNSET:
            field_dict["specification"] = specification
        if link is not UNSET:
            field_dict["link"] = link
        if controlled_vocabulary is not UNSET:
            field_dict["controlledVocabulary"] = controlled_vocabulary
        if allowed_values is not UNSET:
            field_dict["allowedValues"] = allowed_values
        if multiple is not UNSET:
            field_dict["multiple"] = multiple
        if required is not UNSET:
            field_dict["required"] = required
        if sample is not UNSET:
            field_dict["sample"] = sample
        if order is not UNSET:
            field_dict["order"] = order

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        key = d.pop("key", UNSET)

        property_ = d.pop("property", UNSET)

        definition = d.pop("definition", UNSET)

        specification = d.pop("specification", UNSET)

        def _parse_link(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        link = _parse_link(d.pop("link", UNSET))

        def _parse_controlled_vocabulary(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        controlled_vocabulary = _parse_controlled_vocabulary(d.pop("controlledVocabulary", UNSET))

        allowed_values = cast(list[str], d.pop("allowedValues", UNSET))

        multiple = d.pop("multiple", UNSET)

        required = d.pop("required", UNSET)

        sample = d.pop("sample", UNSET)

        order = d.pop("order", UNSET)

        template_property_dto = cls(
            key=key,
            property_=property_,
            definition=definition,
            specification=specification,
            link=link,
            controlled_vocabulary=controlled_vocabulary,
            allowed_values=allowed_values,
            multiple=multiple,
            required=required,
            sample=sample,
            order=order,
        )

        return template_property_dto
