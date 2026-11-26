# SuggestionDto


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**ctid** | **str** |  | 
**type** | **str** |  | 
**property_name** | **str** |  | 
**suggested_value** | **str** |  | 

## Example

```python
from consumer_api_client.models.suggestion_dto import SuggestionDto

# TODO update the JSON string below
json = "{}"
# create an instance of SuggestionDto from a JSON string
suggestion_dto_instance = SuggestionDto.from_json(json)
# print the JSON string representation of the object
print(SuggestionDto.to_json())

# convert the object into a dict
suggestion_dto_dict = suggestion_dto_instance.to_dict()
# create an instance of SuggestionDto from a dict
suggestion_dto_from_dict = SuggestionDto.from_dict(suggestion_dto_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


