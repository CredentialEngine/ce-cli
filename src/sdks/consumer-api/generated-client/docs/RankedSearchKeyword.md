# RankedSearchKeyword


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** |  | [optional] 
**weight** | **float** |  | [optional] 

## Example

```python
from consumer_api_client.models.ranked_search_keyword import RankedSearchKeyword

# TODO update the JSON string below
json = "{}"
# create an instance of RankedSearchKeyword from a JSON string
ranked_search_keyword_instance = RankedSearchKeyword.from_json(json)
# print the JSON string representation of the object
print(RankedSearchKeyword.to_json())

# convert the object into a dict
ranked_search_keyword_dict = ranked_search_keyword_instance.to_dict()
# create an instance of RankedSearchKeyword from a dict
ranked_search_keyword_from_dict = RankedSearchKeyword.from_dict(
    ranked_search_keyword_dict
)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


