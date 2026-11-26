# SearchTotalDto


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **int** |  | [optional] 
**relation** | **str** |  | [optional] 

## Example

```python
from consumer_api_client.models.search_total_dto import SearchTotalDto

# TODO update the JSON string below
json = "{}"
# create an instance of SearchTotalDto from a JSON string
search_total_dto_instance = SearchTotalDto.from_json(json)
# print the JSON string representation of the object
print(SearchTotalDto.to_json())

# convert the object into a dict
search_total_dto_dict = search_total_dto_instance.to_dict()
# create an instance of SearchTotalDto from a dict
search_total_dto_from_dict = SearchTotalDto.from_dict(search_total_dto_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


