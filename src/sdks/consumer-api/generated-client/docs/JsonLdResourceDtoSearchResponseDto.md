# JsonLdResourceDtoSearchResponseDto


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total** | [**SearchTotalDto**](SearchTotalDto.md) |  | [optional] 
**search_took_ms** | **int** |  | [optional] 
**view** | [**SearchResultView**](SearchResultView.md) |  | [optional] 
**results** | [**List[JsonLdResourceDto]**](JsonLdResourceDto.md) |  | [optional] 
**synonyms** | [**SynonymInterpretationDto**](SynonymInterpretationDto.md) |  | [optional] 

## Example

```python
from consumer_api_client.models.json_ld_resource_dto_search_response_dto import (
    JsonLdResourceDtoSearchResponseDto,
)

# TODO update the JSON string below
json = "{}"
# create an instance of JsonLdResourceDtoSearchResponseDto from a JSON string
json_ld_resource_dto_search_response_dto_instance = (
    JsonLdResourceDtoSearchResponseDto.from_json(json)
)
# print the JSON string representation of the object
print(JsonLdResourceDtoSearchResponseDto.to_json())

# convert the object into a dict
json_ld_resource_dto_search_response_dto_dict = (
    json_ld_resource_dto_search_response_dto_instance.to_dict()
)
# create an instance of JsonLdResourceDtoSearchResponseDto from a dict
json_ld_resource_dto_search_response_dto_from_dict = (
    JsonLdResourceDtoSearchResponseDto.from_dict(
        json_ld_resource_dto_search_response_dto_dict
    )
)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


