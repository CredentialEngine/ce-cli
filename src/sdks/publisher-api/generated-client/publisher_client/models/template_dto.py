from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.template_section_dto import TemplateSectionDto


T = TypeVar("T", bound="TemplateDto")


@_attrs_define
class TemplateDto:
    """
    Attributes:
        resource_type (str | Unset):
        sections (list[TemplateSectionDto] | Unset):
    """

    resource_type: str | Unset = UNSET
    sections: list[TemplateSectionDto] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        resource_type = self.resource_type

        sections: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.sections, Unset):
            sections = []
            for sections_item_data in self.sections:
                sections_item = sections_item_data.to_dict()
                sections.append(sections_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if resource_type is not UNSET:
            field_dict["resourceType"] = resource_type
        if sections is not UNSET:
            field_dict["sections"] = sections

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.template_section_dto import TemplateSectionDto  # noqa: PLC0415

        d = dict(src_dict)
        resource_type = d.pop("resourceType", UNSET)

        _sections = d.pop("sections", UNSET)
        sections: list[TemplateSectionDto] | Unset = UNSET
        if _sections is not UNSET:
            sections = []
            for sections_item_data in _sections:
                sections_item = TemplateSectionDto.from_dict(sections_item_data)

                sections.append(sections_item)

        template_dto = cls(
            resource_type=resource_type,
            sections=sections,
        )

        return template_dto
