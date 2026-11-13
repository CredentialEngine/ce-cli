from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from dateutil.parser import isoparse
from typing import cast
from typing import Union
import datetime






T = TypeVar("T", bound="ChangesetUploadResultDto")



@_attrs_define
class ChangesetUploadResultDto:
    """ 
        Attributes:
            community (str):
            tenant (str):
            source_key (str):
            container_name (str):
            blob_path (str):
            file_name (str):
            changeset_uri (str):
            target_data_uri (str):
            archive_target_uri (str):
            workflow_name (str):
            size_bytes (Union[Unset, int]):
            archive_file_count (Union[Unset, int]):
            archive_uncompressed_bytes (Union[Unset, int]):
            received_at_utc (Union[Unset, datetime.datetime]):
     """

    community: str
    tenant: str
    source_key: str
    container_name: str
    blob_path: str
    file_name: str
    changeset_uri: str
    target_data_uri: str
    archive_target_uri: str
    workflow_name: str
    size_bytes: Union[Unset, int] = UNSET
    archive_file_count: Union[Unset, int] = UNSET
    archive_uncompressed_bytes: Union[Unset, int] = UNSET
    received_at_utc: Union[Unset, datetime.datetime] = UNSET





    def to_dict(self) -> dict[str, Any]:
        community = self.community

        tenant = self.tenant

        source_key = self.source_key

        container_name = self.container_name

        blob_path = self.blob_path

        file_name = self.file_name

        changeset_uri = self.changeset_uri

        target_data_uri = self.target_data_uri

        archive_target_uri = self.archive_target_uri

        workflow_name = self.workflow_name

        size_bytes = self.size_bytes

        archive_file_count = self.archive_file_count

        archive_uncompressed_bytes = self.archive_uncompressed_bytes

        received_at_utc: Union[Unset, str] = UNSET
        if not isinstance(self.received_at_utc, Unset):
            received_at_utc = self.received_at_utc.isoformat()


        field_dict: dict[str, Any] = {}

        field_dict.update({
            "community": community,
            "tenant": tenant,
            "sourceKey": source_key,
            "containerName": container_name,
            "blobPath": blob_path,
            "fileName": file_name,
            "changesetUri": changeset_uri,
            "targetDataUri": target_data_uri,
            "archiveTargetUri": archive_target_uri,
            "workflowName": workflow_name,
        })
        if size_bytes is not UNSET:
            field_dict["sizeBytes"] = size_bytes
        if archive_file_count is not UNSET:
            field_dict["archiveFileCount"] = archive_file_count
        if archive_uncompressed_bytes is not UNSET:
            field_dict["archiveUncompressedBytes"] = archive_uncompressed_bytes
        if received_at_utc is not UNSET:
            field_dict["receivedAtUtc"] = received_at_utc

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        community = d.pop("community")

        tenant = d.pop("tenant")

        source_key = d.pop("sourceKey")

        container_name = d.pop("containerName")

        blob_path = d.pop("blobPath")

        file_name = d.pop("fileName")

        changeset_uri = d.pop("changesetUri")

        target_data_uri = d.pop("targetDataUri")

        archive_target_uri = d.pop("archiveTargetUri")

        workflow_name = d.pop("workflowName")

        size_bytes = d.pop("sizeBytes", UNSET)

        archive_file_count = d.pop("archiveFileCount", UNSET)

        archive_uncompressed_bytes = d.pop("archiveUncompressedBytes", UNSET)

        _received_at_utc = d.pop("receivedAtUtc", UNSET)
        received_at_utc: Union[Unset, datetime.datetime]
        if isinstance(_received_at_utc,  Unset):
            received_at_utc = UNSET
        else:
            received_at_utc = isoparse(_received_at_utc)




        changeset_upload_result_dto = cls(
            community=community,
            tenant=tenant,
            source_key=source_key,
            container_name=container_name,
            blob_path=blob_path,
            file_name=file_name,
            changeset_uri=changeset_uri,
            target_data_uri=target_data_uri,
            archive_target_uri=archive_target_uri,
            workflow_name=workflow_name,
            size_bytes=size_bytes,
            archive_file_count=archive_file_count,
            archive_uncompressed_bytes=archive_uncompressed_bytes,
            received_at_utc=received_at_utc,
        )

        return changeset_upload_result_dto

