# ExportDownloadsResponseDto


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**version** | **int** |  | [optional] 
**generated_at** | **datetime** |  | [optional] 
**zip_batch_size** | **int** |  | [optional] 
**exported_resource_count** | **int** |  | [optional] 
**error_count** | **int** |  | [optional] 
**folders** | [**List[ExportDownloadFolderDto]**](ExportDownloadFolderDto.md) |  | [optional] 

## Example

```python
from consumer_api_client.models.export_downloads_response_dto import (
    ExportDownloadsResponseDto,
)

# TODO update the JSON string below
json = "{}"
# create an instance of ExportDownloadsResponseDto from a JSON string
export_downloads_response_dto_instance = ExportDownloadsResponseDto.from_json(json)
# print the JSON string representation of the object
print(ExportDownloadsResponseDto.to_json())

# convert the object into a dict
export_downloads_response_dto_dict = export_downloads_response_dto_instance.to_dict()
# create an instance of ExportDownloadsResponseDto from a dict
export_downloads_response_dto_from_dict = ExportDownloadsResponseDto.from_dict(
    export_downloads_response_dto_dict
)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


