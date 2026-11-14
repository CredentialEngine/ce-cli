from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.template_property_dto import TemplatePropertyDto


T = TypeVar("T", bound="TemplateSectionDto")


@_attrs_define
class TemplateSectionDto:
    """
    Attributes:
        id (Union[Unset, str]):
        title (Union[Unset, str]):
        order (Union[Unset, int]):
        properties (Union[Unset, list['TemplatePropertyDto']]):
    """

    id: Union[Unset, str] = UNSET
    title: Union[Unset, str] = UNSET
    order: Union[Unset, int] = UNSET
    properties: Union[Unset, list["TemplatePropertyDto"]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        title = self.title

        order = self.order

        properties: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.properties, Unset):
            properties = []
            for properties_item_data in self.properties:
                properties_item = properties_item_data.to_dict()
                properties.append(properties_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if title is not UNSET:
            field_dict["title"] = title
        if order is not UNSET:
            field_dict["order"] = order
        if properties is not UNSET:
            field_dict["properties"] = properties

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.template_property_dto import TemplatePropertyDto

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        title = d.pop("title", UNSET)

        order = d.pop("order", UNSET)

        properties = []
        _properties = d.pop("properties", UNSET)
        for properties_item_data in _properties or []:
            properties_item = TemplatePropertyDto.from_dict(properties_item_data)

            properties.append(properties_item)

        template_section_dto = cls(
            id=id,
            title=title,
            order=order,
            properties=properties,
        )

        return template_section_dto
