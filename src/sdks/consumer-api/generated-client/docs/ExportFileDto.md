# ExportFileDto


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**file_name** | **str** |  | 
**download_url** | **str** |  | 

## Example

```python
from consumer_api_client.models.export_file_dto import ExportFileDto

# TODO update the JSON string below
json = "{}"
# create an instance of ExportFileDto from a JSON string
export_file_dto_instance = ExportFileDto.from_json(json)
# print the JSON string representation of the object
print(ExportFileDto.to_json())

# convert the object into a dict
export_file_dto_dict = export_file_dto_instance.to_dict()
# create an instance of ExportFileDto from a dict
export_file_dto_from_dict = ExportFileDto.from_dict(export_file_dto_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


