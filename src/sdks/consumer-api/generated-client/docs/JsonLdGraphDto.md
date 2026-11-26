# JsonLdGraphDto


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**properties** | **Dict[str, Optional[object]]** |  | [optional] 

## Example

```python
from consumer_api_client.models.json_ld_graph_dto import JsonLdGraphDto

# TODO update the JSON string below
json = "{}"
# create an instance of JsonLdGraphDto from a JSON string
json_ld_graph_dto_instance = JsonLdGraphDto.from_json(json)
# print the JSON string representation of the object
print(JsonLdGraphDto.to_json())

# convert the object into a dict
json_ld_graph_dto_dict = json_ld_graph_dto_instance.to_dict()
# create an instance of JsonLdGraphDto from a dict
json_ld_graph_dto_from_dict = JsonLdGraphDto.from_dict(json_ld_graph_dto_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


