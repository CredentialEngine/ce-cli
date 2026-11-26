# SynonymAlternativeDto


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**query** | **str** |  | [optional] 
**expansion** | **str** |  | [optional] 
**acronym** | **str** |  | [optional] 
**source_ids** | **List[str]** |  | [optional] 
**similarity** | **float** |  | [optional] 

## Example

```python
from consumer_api_client.models.synonym_alternative_dto import SynonymAlternativeDto

# TODO update the JSON string below
json = "{}"
# create an instance of SynonymAlternativeDto from a JSON string
synonym_alternative_dto_instance = SynonymAlternativeDto.from_json(json)
# print the JSON string representation of the object
print(SynonymAlternativeDto.to_json())

# convert the object into a dict
synonym_alternative_dto_dict = synonym_alternative_dto_instance.to_dict()
# create an instance of SynonymAlternativeDto from a dict
synonym_alternative_dto_from_dict = SynonymAlternativeDto.from_dict(
    synonym_alternative_dto_dict
)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


