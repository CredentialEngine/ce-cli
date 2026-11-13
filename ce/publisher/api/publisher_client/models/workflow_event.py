from collections.abc import Mapping
from typing import Any, TypeVar, Optional, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast, Union
from typing import Union






T = TypeVar("T", bound="WorkflowEvent")



@_attrs_define
class WorkflowEvent:
    """ 
        Attributes:
            workflow_name (str):
            status (str):
            tenant (str):
            export_id (Union[None, Unset, str]):
            result_folder (Union[None, Unset, str]):
            error (Union[None, Unset, str]):
     """

    workflow_name: str
    status: str
    tenant: str
    export_id: Union[None, Unset, str] = UNSET
    result_folder: Union[None, Unset, str] = UNSET
    error: Union[None, Unset, str] = UNSET





    def to_dict(self) -> dict[str, Any]:
        workflow_name = self.workflow_name

        status = self.status

        tenant = self.tenant

        export_id: Union[None, Unset, str]
        if isinstance(self.export_id, Unset):
            export_id = UNSET
        else:
            export_id = self.export_id

        result_folder: Union[None, Unset, str]
        if isinstance(self.result_folder, Unset):
            result_folder = UNSET
        else:
            result_folder = self.result_folder

        error: Union[None, Unset, str]
        if isinstance(self.error, Unset):
            error = UNSET
        else:
            error = self.error


        field_dict: dict[str, Any] = {}

        field_dict.update({
            "workflowName": workflow_name,
            "status": status,
            "tenant": tenant,
        })
        if export_id is not UNSET:
            field_dict["exportId"] = export_id
        if result_folder is not UNSET:
            field_dict["resultFolder"] = result_folder
        if error is not UNSET:
            field_dict["error"] = error

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        workflow_name = d.pop("workflowName")

        status = d.pop("status")

        tenant = d.pop("tenant")

        def _parse_export_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        export_id = _parse_export_id(d.pop("exportId", UNSET))


        def _parse_result_folder(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        result_folder = _parse_result_folder(d.pop("resultFolder", UNSET))


        def _parse_error(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        error = _parse_error(d.pop("error", UNSET))


        workflow_event = cls(
            workflow_name=workflow_name,
            status=status,
            tenant=tenant,
            export_id=export_id,
            result_folder=result_folder,
            error=error,
        )

        return workflow_event

