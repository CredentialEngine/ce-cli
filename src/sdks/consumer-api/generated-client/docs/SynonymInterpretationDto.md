# SynonymInterpretationDto


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**original_query** | **str** |  | [optional] 
**is_ambiguous** | **bool** |  | [optional] 
**keywords** | [**List[RankedSearchKeyword]**](RankedSearchKeyword.md) |  | [optional] 
**alternatives** | [**List[SynonymAlternativeDto]**](SynonymAlternativeDto.md) |  | [optional] 

## Example

```python
from consumer_api_client.models.synonym_interpretation_dto import (
    SynonymInterpretationDto,
)

# TODO update the JSON string below
json = "{}"
# create an instance of SynonymInterpretationDto from a JSON string
synonym_interpretation_dto_instance = SynonymInterpretationDto.from_json(json)
# print the JSON string representation of the object
print(SynonymInterpretationDto.to_json())

# convert the object into a dict
synonym_interpretation_dto_dict = synonym_interpretation_dto_instance.to_dict()
# create an instance of SynonymInterpretationDto from a dict
synonym_interpretation_dto_from_dict = SynonymInterpretationDto.from_dict(
    synonym_interpretation_dto_dict
)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


