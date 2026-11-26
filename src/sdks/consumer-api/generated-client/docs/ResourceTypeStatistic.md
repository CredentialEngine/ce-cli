# ResourceTypeStatistic


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** |  | [optional] 
**label** | **str** |  | [optional] 
**count** | **int** |  | [optional] 
**exact_count** | **int** |  | [optional] 
**has_children** | **bool** |  | [optional] 
**children** | [**List[ResourceTypeStatistic]**](ResourceTypeStatistic.md) |  | [optional] 

## Example

```python
from consumer_api_client.models.resource_type_statistic import ResourceTypeStatistic

# TODO update the JSON string below
json = "{}"
# create an instance of ResourceTypeStatistic from a JSON string
resource_type_statistic_instance = ResourceTypeStatistic.from_json(json)
# print the JSON string representation of the object
print(ResourceTypeStatistic.to_json())

# convert the object into a dict
resource_type_statistic_dict = resource_type_statistic_instance.to_dict()
# create an instance of ResourceTypeStatistic from a dict
resource_type_statistic_from_dict = ResourceTypeStatistic.from_dict(
    resource_type_statistic_dict
)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


