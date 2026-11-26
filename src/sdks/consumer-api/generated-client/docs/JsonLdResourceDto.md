# JsonLdResourceDto


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**properties** | **Dict[str, Optional[object]]** |  | [optional] 

## Example

```python
from consumer_api_client.models.json_ld_resource_dto import JsonLdResourceDto

# TODO update the JSON string below
json = "{}"
# create an instance of JsonLdResourceDto from a JSON string
json_ld_resource_dto_instance = JsonLdResourceDto.from_json(json)
# print the JSON string representation of the object
print(JsonLdResourceDto.to_json())

# convert the object into a dict
json_ld_resource_dto_dict = json_ld_resource_dto_instance.to_dict()
# create an instance of JsonLdResourceDto from a dict
json_ld_resource_dto_from_dict = JsonLdResourceDto.from_dict(json_ld_resource_dto_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


