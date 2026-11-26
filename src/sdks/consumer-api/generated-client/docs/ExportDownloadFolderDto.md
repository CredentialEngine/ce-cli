# ExportDownloadFolderDto


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**folder** | **str** |  | 
**type** | **str** |  | [optional] 
**file_count** | **int** |  | [optional] 
**zip_count** | **int** |  | [optional] 
**archives** | [**List[ExportDownloadArchiveDto]**](ExportDownloadArchiveDto.md) |  | [optional] 

## Example

```python
from consumer_api_client.models.export_download_folder_dto import (
    ExportDownloadFolderDto,
)

# TODO update the JSON string below
json = "{}"
# create an instance of ExportDownloadFolderDto from a JSON string
export_download_folder_dto_instance = ExportDownloadFolderDto.from_json(json)
# print the JSON string representation of the object
print(ExportDownloadFolderDto.to_json())

# convert the object into a dict
export_download_folder_dto_dict = export_download_folder_dto_instance.to_dict()
# create an instance of ExportDownloadFolderDto from a dict
export_download_folder_dto_from_dict = ExportDownloadFolderDto.from_dict(
    export_download_folder_dto_dict
)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


