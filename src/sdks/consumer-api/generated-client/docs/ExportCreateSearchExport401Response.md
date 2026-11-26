# ExportCreateSearchExport401Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**discriminator_type** | **str** |  | 
**type** | **str** |  | [optional] 
**title** | **str** |  | [optional] 
**status** | **int** |  | [optional] 
**detail** | **str** |  | [optional] 
**instance** | **str** |  | [optional] 
**errors** | **Dict[str, List[str]]** |  | [optional] 

## Example

```python
from consumer_api_client.models.export_create_search_export401_response import (
    ExportCreateSearchExport401Response,
)

# TODO update the JSON string below
json = "{}"
# create an instance of ExportCreateSearchExport401Response from a JSON string
export_create_search_export401_response_instance = (
    ExportCreateSearchExport401Response.from_json(json)
)
# print the JSON string representation of the object
print(ExportCreateSearchExport401Response.to_json())

# convert the object into a dict
export_create_search_export401_response_dict = (
    export_create_search_export401_response_instance.to_dict()
)
# create an instance of ExportCreateSearchExport401Response from a dict
export_create_search_export401_response_from_dict = (
    ExportCreateSearchExport401Response.from_dict(
        export_create_search_export401_response_dict
    )
)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


