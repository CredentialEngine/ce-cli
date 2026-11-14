from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.template_section_dto import TemplateSectionDto


T = TypeVar("T", bound="TemplateDto")


@_attrs_define
class TemplateDto:
    """
    Attributes:
        resource_type (Union[Unset, str]):
        sections (Union[Unset, list['TemplateSectionDto']]):
    """

    resource_type: Union[Unset, str] = UNSET
    sections: Union[Unset, list["TemplateSectionDto"]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        resource_type = self.resource_type

        sections: Union[Unset, list[dict[str, Any]]] = UNSET
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
        from ..models.template_section_dto import TemplateSectionDto

        d = dict(src_dict)
        resource_type = d.pop("resourceType", UNSET)

        sections = []
        _sections = d.pop("sections", UNSET)
        for sections_item_data in _sections or []:
            sections_item = TemplateSectionDto.from_dict(sections_item_data)

            sections.append(sections_item)

        template_dto = cls(
            resource_type=resource_type,
            sections=sections,
        )

        return template_dto
