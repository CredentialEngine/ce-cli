# MetadataDto


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**properties** | **Dict[str, Optional[object]]** |  | [optional] 

## Example

```python
from consumer_api_client.models.metadata_dto import MetadataDto

# TODO update the JSON string below
json = "{}"
# create an instance of MetadataDto from a JSON string
metadata_dto_instance = MetadataDto.from_json(json)
# print the JSON string representation of the object
print(MetadataDto.to_json())

# convert the object into a dict
metadata_dto_dict = metadata_dto_instance.to_dict()
# create an instance of MetadataDto from a dict
metadata_dto_from_dict = MetadataDto.from_dict(metadata_dto_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


