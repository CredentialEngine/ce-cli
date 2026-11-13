from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
from typing import cast, Union
from typing import Union

if TYPE_CHECKING:
  from ..models.manual_entry_credit_value_dto import ManualEntryCreditValueDto
  from ..models.manual_entry_identifier_dto import ManualEntryIdentifierDto
  from ..models.manual_entry_duration_dto import ManualEntryDurationDto
  from ..models.manual_entry_jurisdiction_dto import ManualEntryJurisdictionDto





T = TypeVar("T", bound="CreateLearningOpportunityManualEntryDto")



@_attrs_define
class CreateLearningOpportunityManualEntryDto:
    """ 
        Attributes:
            primary_organization (str):
            learning_type (str):
            name (str):
            description (str):
            subject_webpage (str):
            life_cycle_status_type (str):
            language (str):
            offered_by_primary_organization (Union[Unset, bool]):
            external_identifier (Union[None, Unset, str]):
            available_online_at (Union[None, Unset, str]):
            availability_listing (Union[None, Unset, str]):
            in_catalog (Union[None, Unset, str]):
            is_non_credit (Union[None, Unset, bool]):
            is_registered_apprenticeship (Union[None, Unset, bool]):
            coded_notation (Union[None, Unset, str]):
            identifiers (Union[Unset, list['ManualEntryIdentifierDto']]):
            version_identifiers (Union[Unset, list['ManualEntryIdentifierDto']]):
            alternate_names (Union[Unset, list[str]]):
            subjects (Union[Unset, list[str]]):
            keywords (Union[Unset, list[str]]):
            audience_level_types (Union[Unset, list[str]]):
            audience_types (Union[Unset, list[str]]):
            delivery_types (Union[Unset, list[str]]):
            delivery_type_description (Union[None, Unset, str]):
            learning_method_types (Union[Unset, list[str]]):
            learning_method_description (Union[None, Unset, str]):
            estimated_duration (Union[Unset, ManualEntryDurationDto]):
            jurisdictions (Union[Unset, list['ManualEntryJurisdictionDto']]):
            credit_value (Union[Unset, ManualEntryCreditValueDto]):
            date_effective (Union[None, Unset, str]):
            expiration_date (Union[None, Unset, str]):
     """

    primary_organization: str
    learning_type: str
    name: str
    description: str
    subject_webpage: str
    life_cycle_status_type: str
    language: str
    offered_by_primary_organization: Union[Unset, bool] = UNSET
    external_identifier: Union[None, Unset, str] = UNSET
    available_online_at: Union[None, Unset, str] = UNSET
    availability_listing: Union[None, Unset, str] = UNSET
    in_catalog: Union[None, Unset, str] = UNSET
    is_non_credit: Union[None, Unset, bool] = UNSET
    is_registered_apprenticeship: Union[None, Unset, bool] = UNSET
    coded_notation: Union[None, Unset, str] = UNSET
    identifiers: Union[Unset, list['ManualEntryIdentifierDto']] = UNSET
    version_identifiers: Union[Unset, list['ManualEntryIdentifierDto']] = UNSET
    alternate_names: Union[Unset, list[str]] = UNSET
    subjects: Union[Unset, list[str]] = UNSET
    keywords: Union[Unset, list[str]] = UNSET
    audience_level_types: Union[Unset, list[str]] = UNSET
    audience_types: Union[Unset, list[str]] = UNSET
    delivery_types: Union[Unset, list[str]] = UNSET
    delivery_type_description: Union[None, Unset, str] = UNSET
    learning_method_types: Union[Unset, list[str]] = UNSET
    learning_method_description: Union[None, Unset, str] = UNSET
    estimated_duration: Union[Unset, 'ManualEntryDurationDto'] = UNSET
    jurisdictions: Union[Unset, list['ManualEntryJurisdictionDto']] = UNSET
    credit_value: Union[Unset, 'ManualEntryCreditValueDto'] = UNSET
    date_effective: Union[None, Unset, str] = UNSET
    expiration_date: Union[None, Unset, str] = UNSET





    def to_dict(self) -> dict[str, Any]:
        from ..models.manual_entry_credit_value_dto import ManualEntryCreditValueDto
        from ..models.manual_entry_identifier_dto import ManualEntryIdentifierDto
        from ..models.manual_entry_duration_dto import ManualEntryDurationDto
        from ..models.manual_entry_jurisdiction_dto import ManualEntryJurisdictionDto
        primary_organization = self.primary_organization

        learning_type = self.learning_type

        name = self.name

        description = self.description

        subject_webpage = self.subject_webpage

        life_cycle_status_type = self.life_cycle_status_type

        language = self.language

        offered_by_primary_organization = self.offered_by_primary_organization

        external_identifier: Union[None, Unset, str]
        if isinstance(self.external_identifier, Unset):
            external_identifier = UNSET
        else:
            external_identifier = self.external_identifier

        available_online_at: Union[None, Unset, str]
        if isinstance(self.available_online_at, Unset):
            available_online_at = UNSET
        else:
            available_online_at = self.available_online_at

        availability_listing: Union[None, Unset, str]
        if isinstance(self.availability_listing, Unset):
            availability_listing = UNSET
        else:
            availability_listing = self.availability_listing

        in_catalog: Union[None, Unset, str]
        if isinstance(self.in_catalog, Unset):
            in_catalog = UNSET
        else:
            in_catalog = self.in_catalog

        is_non_credit: Union[None, Unset, bool]
        if isinstance(self.is_non_credit, Unset):
            is_non_credit = UNSET
        else:
            is_non_credit = self.is_non_credit

        is_registered_apprenticeship: Union[None, Unset, bool]
        if isinstance(self.is_registered_apprenticeship, Unset):
            is_registered_apprenticeship = UNSET
        else:
            is_registered_apprenticeship = self.is_registered_apprenticeship

        coded_notation: Union[None, Unset, str]
        if isinstance(self.coded_notation, Unset):
            coded_notation = UNSET
        else:
            coded_notation = self.coded_notation

        identifiers: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.identifiers, Unset):
            identifiers = []
            for identifiers_item_data in self.identifiers:
                identifiers_item = identifiers_item_data.to_dict()
                identifiers.append(identifiers_item)



        version_identifiers: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.version_identifiers, Unset):
            version_identifiers = []
            for version_identifiers_item_data in self.version_identifiers:
                version_identifiers_item = version_identifiers_item_data.to_dict()
                version_identifiers.append(version_identifiers_item)



        alternate_names: Union[Unset, list[str]] = UNSET
        if not isinstance(self.alternate_names, Unset):
            alternate_names = self.alternate_names



        subjects: Union[Unset, list[str]] = UNSET
        if not isinstance(self.subjects, Unset):
            subjects = self.subjects



        keywords: Union[Unset, list[str]] = UNSET
        if not isinstance(self.keywords, Unset):
            keywords = self.keywords



        audience_level_types: Union[Unset, list[str]] = UNSET
        if not isinstance(self.audience_level_types, Unset):
            audience_level_types = self.audience_level_types



        audience_types: Union[Unset, list[str]] = UNSET
        if not isinstance(self.audience_types, Unset):
            audience_types = self.audience_types



        delivery_types: Union[Unset, list[str]] = UNSET
        if not isinstance(self.delivery_types, Unset):
            delivery_types = self.delivery_types



        delivery_type_description: Union[None, Unset, str]
        if isinstance(self.delivery_type_description, Unset):
            delivery_type_description = UNSET
        else:
            delivery_type_description = self.delivery_type_description

        learning_method_types: Union[Unset, list[str]] = UNSET
        if not isinstance(self.learning_method_types, Unset):
            learning_method_types = self.learning_method_types



        learning_method_description: Union[None, Unset, str]
        if isinstance(self.learning_method_description, Unset):
            learning_method_description = UNSET
        else:
            learning_method_description = self.learning_method_description

        estimated_duration: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.estimated_duration, Unset):
            estimated_duration = self.estimated_duration.to_dict()

        jurisdictions: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.jurisdictions, Unset):
            jurisdictions = []
            for jurisdictions_item_data in self.jurisdictions:
                jurisdictions_item = jurisdictions_item_data.to_dict()
                jurisdictions.append(jurisdictions_item)



        credit_value: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.credit_value, Unset):
            credit_value = self.credit_value.to_dict()

        date_effective: Union[None, Unset, str]
        if isinstance(self.date_effective, Unset):
            date_effective = UNSET
        else:
            date_effective = self.date_effective

        expiration_date: Union[None, Unset, str]
        if isinstance(self.expiration_date, Unset):
            expiration_date = UNSET
        else:
            expiration_date = self.expiration_date


        field_dict: dict[str, Any] = {}

        field_dict.update({
            "primaryOrganization": primary_organization,
            "learningType": learning_type,
            "name": name,
            "description": description,
            "subjectWebpage": subject_webpage,
            "lifeCycleStatusType": life_cycle_status_type,
            "language": language,
        })
        if offered_by_primary_organization is not UNSET:
            field_dict["offeredByPrimaryOrganization"] = offered_by_primary_organization
        if external_identifier is not UNSET:
            field_dict["externalIdentifier"] = external_identifier
        if available_online_at is not UNSET:
            field_dict["availableOnlineAt"] = available_online_at
        if availability_listing is not UNSET:
            field_dict["availabilityListing"] = availability_listing
        if in_catalog is not UNSET:
            field_dict["inCatalog"] = in_catalog
        if is_non_credit is not UNSET:
            field_dict["isNonCredit"] = is_non_credit
        if is_registered_apprenticeship is not UNSET:
            field_dict["isRegisteredApprenticeship"] = is_registered_apprenticeship
        if coded_notation is not UNSET:
            field_dict["codedNotation"] = coded_notation
        if identifiers is not UNSET:
            field_dict["identifiers"] = identifiers
        if version_identifiers is not UNSET:
            field_dict["versionIdentifiers"] = version_identifiers
        if alternate_names is not UNSET:
            field_dict["alternateNames"] = alternate_names
        if subjects is not UNSET:
            field_dict["subjects"] = subjects
        if keywords is not UNSET:
            field_dict["keywords"] = keywords
        if audience_level_types is not UNSET:
            field_dict["audienceLevelTypes"] = audience_level_types
        if audience_types is not UNSET:
            field_dict["audienceTypes"] = audience_types
        if delivery_types is not UNSET:
            field_dict["deliveryTypes"] = delivery_types
        if delivery_type_description is not UNSET:
            field_dict["deliveryTypeDescription"] = delivery_type_description
        if learning_method_types is not UNSET:
            field_dict["learningMethodTypes"] = learning_method_types
        if learning_method_description is not UNSET:
            field_dict["learningMethodDescription"] = learning_method_description
        if estimated_duration is not UNSET:
            field_dict["estimatedDuration"] = estimated_duration
        if jurisdictions is not UNSET:
            field_dict["jurisdictions"] = jurisdictions
        if credit_value is not UNSET:
            field_dict["creditValue"] = credit_value
        if date_effective is not UNSET:
            field_dict["dateEffective"] = date_effective
        if expiration_date is not UNSET:
            field_dict["expirationDate"] = expiration_date

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.manual_entry_credit_value_dto import ManualEntryCreditValueDto
        from ..models.manual_entry_identifier_dto import ManualEntryIdentifierDto
        from ..models.manual_entry_duration_dto import ManualEntryDurationDto
        from ..models.manual_entry_jurisdiction_dto import ManualEntryJurisdictionDto
        d = dict(src_dict)
        primary_organization = d.pop("primaryOrganization")

        learning_type = d.pop("learningType")

        name = d.pop("name")

        description = d.pop("description")

        subject_webpage = d.pop("subjectWebpage")

        life_cycle_status_type = d.pop("lifeCycleStatusType")

        language = d.pop("language")

        offered_by_primary_organization = d.pop("offeredByPrimaryOrganization", UNSET)

        def _parse_external_identifier(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        external_identifier = _parse_external_identifier(d.pop("externalIdentifier", UNSET))


        def _parse_available_online_at(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        available_online_at = _parse_available_online_at(d.pop("availableOnlineAt", UNSET))


        def _parse_availability_listing(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        availability_listing = _parse_availability_listing(d.pop("availabilityListing", UNSET))


        def _parse_in_catalog(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        in_catalog = _parse_in_catalog(d.pop("inCatalog", UNSET))


        def _parse_is_non_credit(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        is_non_credit = _parse_is_non_credit(d.pop("isNonCredit", UNSET))


        def _parse_is_registered_apprenticeship(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        is_registered_apprenticeship = _parse_is_registered_apprenticeship(d.pop("isRegisteredApprenticeship", UNSET))


        def _parse_coded_notation(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        coded_notation = _parse_coded_notation(d.pop("codedNotation", UNSET))


        identifiers = []
        _identifiers = d.pop("identifiers", UNSET)
        for identifiers_item_data in (_identifiers or []):
            identifiers_item = ManualEntryIdentifierDto.from_dict(identifiers_item_data)



            identifiers.append(identifiers_item)


        version_identifiers = []
        _version_identifiers = d.pop("versionIdentifiers", UNSET)
        for version_identifiers_item_data in (_version_identifiers or []):
            version_identifiers_item = ManualEntryIdentifierDto.from_dict(version_identifiers_item_data)



            version_identifiers.append(version_identifiers_item)


        alternate_names = cast(list[str], d.pop("alternateNames", UNSET))


        subjects = cast(list[str], d.pop("subjects", UNSET))


        keywords = cast(list[str], d.pop("keywords", UNSET))


        audience_level_types = cast(list[str], d.pop("audienceLevelTypes", UNSET))


        audience_types = cast(list[str], d.pop("audienceTypes", UNSET))


        delivery_types = cast(list[str], d.pop("deliveryTypes", UNSET))


        def _parse_delivery_type_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        delivery_type_description = _parse_delivery_type_description(d.pop("deliveryTypeDescription", UNSET))


        learning_method_types = cast(list[str], d.pop("learningMethodTypes", UNSET))


        def _parse_learning_method_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        learning_method_description = _parse_learning_method_description(d.pop("learningMethodDescription", UNSET))


        _estimated_duration = d.pop("estimatedDuration", UNSET)
        estimated_duration: Union[Unset, ManualEntryDurationDto]
        if isinstance(_estimated_duration,  Unset):
            estimated_duration = UNSET
        else:
            estimated_duration = ManualEntryDurationDto.from_dict(_estimated_duration)




        jurisdictions = []
        _jurisdictions = d.pop("jurisdictions", UNSET)
        for jurisdictions_item_data in (_jurisdictions or []):
            jurisdictions_item = ManualEntryJurisdictionDto.from_dict(jurisdictions_item_data)



            jurisdictions.append(jurisdictions_item)


        _credit_value = d.pop("creditValue", UNSET)
        credit_value: Union[Unset, ManualEntryCreditValueDto]
        if isinstance(_credit_value,  Unset):
            credit_value = UNSET
        else:
            credit_value = ManualEntryCreditValueDto.from_dict(_credit_value)




        def _parse_date_effective(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        date_effective = _parse_date_effective(d.pop("dateEffective", UNSET))


        def _parse_expiration_date(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        expiration_date = _parse_expiration_date(d.pop("expirationDate", UNSET))


        create_learning_opportunity_manual_entry_dto = cls(
            primary_organization=primary_organization,
            learning_type=learning_type,
            name=name,
            description=description,
            subject_webpage=subject_webpage,
            life_cycle_status_type=life_cycle_status_type,
            language=language,
            offered_by_primary_organization=offered_by_primary_organization,
            external_identifier=external_identifier,
            available_online_at=available_online_at,
            availability_listing=availability_listing,
            in_catalog=in_catalog,
            is_non_credit=is_non_credit,
            is_registered_apprenticeship=is_registered_apprenticeship,
            coded_notation=coded_notation,
            identifiers=identifiers,
            version_identifiers=version_identifiers,
            alternate_names=alternate_names,
            subjects=subjects,
            keywords=keywords,
            audience_level_types=audience_level_types,
            audience_types=audience_types,
            delivery_types=delivery_types,
            delivery_type_description=delivery_type_description,
            learning_method_types=learning_method_types,
            learning_method_description=learning_method_description,
            estimated_duration=estimated_duration,
            jurisdictions=jurisdictions,
            credit_value=credit_value,
            date_effective=date_effective,
            expiration_date=expiration_date,
        )

        return create_learning_opportunity_manual_entry_dto

