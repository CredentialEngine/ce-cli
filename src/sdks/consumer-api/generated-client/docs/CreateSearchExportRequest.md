# CreateSearchExportRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**url** | **str** |  | 
**zip_batch_size** | **int** |  | [optional] [default to 25000]

## Example

```python
from consumer_api_client.models.create_search_export_request import (
    CreateSearchExportRequest,
)

# TODO update the JSON string below
json = "{}"
# create an instance of CreateSearchExportRequest from a JSON string
create_search_export_request_instance = CreateSearchExportRequest.from_json(json)
# print the JSON string representation of the object
print(CreateSearchExportRequest.to_json())

# convert the object into a dict
create_search_export_request_dict = create_search_export_request_instance.to_dict()
# create an instance of CreateSearchExportRequest from a dict
create_search_export_request_from_dict = CreateSearchExportRequest.from_dict(
    create_search_export_request_dict
)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


