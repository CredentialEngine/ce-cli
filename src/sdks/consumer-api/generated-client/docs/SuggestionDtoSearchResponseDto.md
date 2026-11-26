# SuggestionDtoSearchResponseDto


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total** | [**SearchTotalDto**](SearchTotalDto.md) |  | [optional] 
**search_took_ms** | **int** |  | [optional] 
**view** | [**SearchResultView**](SearchResultView.md) |  | [optional] 
**results** | [**List[SuggestionDto]**](SuggestionDto.md) |  | [optional] 
**synonyms** | [**SynonymInterpretationDto**](SynonymInterpretationDto.md) |  | [optional] 

## Example

```python
from consumer_api_client.models.suggestion_dto_search_response_dto import (
    SuggestionDtoSearchResponseDto,
)

# TODO update the JSON string below
json = "{}"
# create an instance of SuggestionDtoSearchResponseDto from a JSON string
suggestion_dto_search_response_dto_instance = SuggestionDtoSearchResponseDto.from_json(
    json
)
# print the JSON string representation of the object
print(SuggestionDtoSearchResponseDto.to_json())

# convert the object into a dict
suggestion_dto_search_response_dto_dict = (
    suggestion_dto_search_response_dto_instance.to_dict()
)
# create an instance of SuggestionDtoSearchResponseDto from a dict
suggestion_dto_search_response_dto_from_dict = SuggestionDtoSearchResponseDto.from_dict(
    suggestion_dto_search_response_dto_dict
)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


