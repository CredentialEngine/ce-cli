from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.audit_event_types import AuditEventTypes
from ..types import UNSET, Unset
from dateutil.parser import isoparse
from typing import cast
from typing import cast, Union
from typing import Union
from uuid import UUID
import datetime

if TYPE_CHECKING:
  from ..models.reviewers_removed_metadata import ReviewersRemovedMetadata
  from ..models.iteration_files_added_metadata import IterationFilesAddedMetadata
  from ..models.reviewers_added_metadata import ReviewersAddedMetadata
  from ..models.iteration_files_deleted_metadata import IterationFilesDeletedMetadata





T = TypeVar("T", bound="ProjectAuditLogDto")



@_attrs_define
class ProjectAuditLogDto:
    """ 
        Attributes:
            id (int):
            project_id (int):
            actor_user_id (UUID):
            created_at (datetime.datetime):
            event_type (AuditEventTypes):
            description (str):
            iteration_id (Union[None, Unset, int]):
            metadata (Union['IterationFilesAddedMetadata', 'IterationFilesDeletedMetadata', 'ReviewersAddedMetadata',
                'ReviewersRemovedMetadata', None, Unset]):
     """

    id: int
    project_id: int
    actor_user_id: UUID
    created_at: datetime.datetime
    event_type: AuditEventTypes
    description: str
    iteration_id: Union[None, Unset, int] = UNSET
    metadata: Union['IterationFilesAddedMetadata', 'IterationFilesDeletedMetadata', 'ReviewersAddedMetadata', 'ReviewersRemovedMetadata', None, Unset] = UNSET





    def to_dict(self) -> dict[str, Any]:
        from ..models.reviewers_removed_metadata import ReviewersRemovedMetadata
        from ..models.iteration_files_added_metadata import IterationFilesAddedMetadata
        from ..models.reviewers_added_metadata import ReviewersAddedMetadata
        from ..models.iteration_files_deleted_metadata import IterationFilesDeletedMetadata
        id = self.id

        project_id = self.project_id

        actor_user_id = str(self.actor_user_id)

        created_at = self.created_at.isoformat()

        event_type = self.event_type.value

        description = self.description

        iteration_id: Union[None, Unset, int]
        if isinstance(self.iteration_id, Unset):
            iteration_id = UNSET
        else:
            iteration_id = self.iteration_id

        metadata: Union[None, Unset, dict[str, Any]]
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, IterationFilesAddedMetadata):
            metadata = self.metadata.to_dict()
        elif isinstance(self.metadata, IterationFilesDeletedMetadata):
            metadata = self.metadata.to_dict()
        elif isinstance(self.metadata, ReviewersAddedMetadata):
            metadata = self.metadata.to_dict()
        elif isinstance(self.metadata, ReviewersRemovedMetadata):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata


        field_dict: dict[str, Any] = {}

        field_dict.update({
            "id": id,
            "projectId": project_id,
            "actorUserId": actor_user_id,
            "createdAt": created_at,
            "eventType": event_type,
            "description": description,
        })
        if iteration_id is not UNSET:
            field_dict["iterationId"] = iteration_id
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.reviewers_removed_metadata import ReviewersRemovedMetadata
        from ..models.iteration_files_added_metadata import IterationFilesAddedMetadata
        from ..models.reviewers_added_metadata import ReviewersAddedMetadata
        from ..models.iteration_files_deleted_metadata import IterationFilesDeletedMetadata
        d = dict(src_dict)
        id = d.pop("id")

        project_id = d.pop("projectId")

        actor_user_id = UUID(d.pop("actorUserId"))




        created_at = isoparse(d.pop("createdAt"))




        event_type = AuditEventTypes(d.pop("eventType"))




        description = d.pop("description")

        def _parse_iteration_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        iteration_id = _parse_iteration_id(d.pop("iterationId", UNSET))


        def _parse_metadata(data: object) -> Union['IterationFilesAddedMetadata', 'IterationFilesDeletedMetadata', 'ReviewersAddedMetadata', 'ReviewersRemovedMetadata', None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = IterationFilesAddedMetadata.from_dict(data)



                return metadata_type_0
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_1 = IterationFilesDeletedMetadata.from_dict(data)



                return metadata_type_1
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_2 = ReviewersAddedMetadata.from_dict(data)



                return metadata_type_2
            except: # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_3 = ReviewersRemovedMetadata.from_dict(data)



                return metadata_type_3
            except: # noqa: E722
                pass
            return cast(Union['IterationFilesAddedMetadata', 'IterationFilesDeletedMetadata', 'ReviewersAddedMetadata', 'ReviewersRemovedMetadata', None, Unset], data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))


        project_audit_log_dto = cls(
            id=id,
            project_id=project_id,
            actor_user_id=actor_user_id,
            created_at=created_at,
            event_type=event_type,
            description=description,
            iteration_id=iteration_id,
            metadata=metadata,
        )

        return project_audit_log_dto

