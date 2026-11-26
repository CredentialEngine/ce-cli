# ResourceIdDto


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | [optional] 
**ctid** | **str** |  | [optional] 

## Example

```python
from consumer_api_client.models.resource_id_dto import ResourceIdDto

# TODO update the JSON string below
json = "{}"
# create an instance of ResourceIdDto from a JSON string
resource_id_dto_instance = ResourceIdDto.from_json(json)
# print the JSON string representation of the object
print(ResourceIdDto.to_json())

# convert the object into a dict
resource_id_dto_dict = resource_id_dto_instance.to_dict()
# create an instance of ResourceIdDto from a dict
resource_id_dto_from_dict = ResourceIdDto.from_dict(resource_id_dto_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


