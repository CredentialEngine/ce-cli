# ExportDownloadArchiveDto


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**path** | **str** |  | 
**file_count** | **int** |  | [optional] 
**download_url** | **str** |  | [optional] 

## Example

```python
from consumer_api_client.models.export_download_archive_dto import (
    ExportDownloadArchiveDto,
)

# TODO update the JSON string below
json = "{}"
# create an instance of ExportDownloadArchiveDto from a JSON string
export_download_archive_dto_instance = ExportDownloadArchiveDto.from_json(json)
# print the JSON string representation of the object
print(ExportDownloadArchiveDto.to_json())

# convert the object into a dict
export_download_archive_dto_dict = export_download_archive_dto_instance.to_dict()
# create an instance of ExportDownloadArchiveDto from a dict
export_download_archive_dto_from_dict = ExportDownloadArchiveDto.from_dict(
    export_download_archive_dto_dict
)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


