# FilterModel


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**var_field** | **str** |  | [optional] 
**operator** | [**Operators**](Operators.md) |  | [optional] 
**value** | **str** |  | [optional] 
**values** | **List[str]** |  | [optional] 

## Example

```python
from consumer_api_client.models.filter_model import FilterModel

# TODO update the JSON string below
json = "{}"
# create an instance of FilterModel from a JSON string
filter_model_instance = FilterModel.from_json(json)
# print the JSON string representation of the object
print(FilterModel.to_json())

# convert the object into a dict
filter_model_dict = filter_model_instance.to_dict()
# create an instance of FilterModel from a dict
filter_model_from_dict = FilterModel.from_dict(filter_model_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


