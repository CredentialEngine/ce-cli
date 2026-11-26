# consumer_api_client.SearchApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**search_search**](SearchApi.md#search_search) | **GET** /search | Search for different resources from the Credential Engine registry.
[**search_suggestions**](SearchApi.md#search_suggestions) | **GET** /search/suggestions | Search for resource suggestions based on the entered query.


# **search_search**
> JsonLdResourceDtoSearchResponseDto search_search(include_bnodes, query=query, type=type, language=language, index_type=index_type, index_id=index_id, page=page, view=view, filters=filters)

Search for different resources from the Credential Engine registry.

Search for resources using:

- A `query`, which is any name, keyword, CTID, etc. A request must contain at least one query or filter.

- A resource `type` (like `ceterms:Credential`). This defaults to all types if not included.

- A `language`, such as `en` (English), `fr` (French), or `es` (Spanish).

- Whether or not to `includeBnodes` in the search results.

- The `index` to query, such as `es` for Elastic Search. Right now only Elastic Search is available here and is the default

- The `indexId` for the index to search (for example, a tenancy id).

- The `page` of results to start with. 0 or leaving it blank will start from the first result.

- The `view` for the response, with more detailed options like `Detail`, or simpler options like `Ids`, which just provides the ids.

- Finally, add `filters` to the query. A request must contain at least one query or filter. 

-- Filters Example: {
  "field": "ceterms:ownedBy",
  "operator": "CONTAINS",
  "value": "ce-5a4615e2-662c-4e87-a655-924b255c5660",
} 

-- Operators include: `MATCHES`, `EQUALS`, `HAS_FIELD`, `CONTAINS`, `IN`, `UNDER`, and `STARTS_WITH`



### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
from consumer_api_client.models.filter_model import FilterModel
from consumer_api_client.models.json_ld_resource_dto_search_response_dto import (
    JsonLdResourceDtoSearchResponseDto,
)
from consumer_api_client.models.search_result_view import SearchResultView
from consumer_api_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = consumer_api_client.Configuration(host="http://localhost")

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
async with consumer_api_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = consumer_api_client.SearchApi(api_client)
    include_bnodes = True  # bool |
    query = "query_example"  # str |  (optional)
    type = "type_example"  # str |  (optional)
    language = "language_example"  # str |  (optional)
    index_type = "index_type_example"  # str |  (optional)
    index_id = "index_id_example"  # str |  (optional)
    page = 56  # int |  (optional)
    view = consumer_api_client.SearchResultView()  # SearchResultView |  (optional)
    filters = [consumer_api_client.FilterModel()]  # List[FilterModel] |  (optional)

    try:
        # Search for different resources from the Credential Engine registry.
        api_response = await api_instance.search_search(
            include_bnodes,
            query=query,
            type=type,
            language=language,
            index_type=index_type,
            index_id=index_id,
            page=page,
            view=view,
            filters=filters,
        )
        print("The response of SearchApi->search_search:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SearchApi->search_search: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **include_bnodes** | **bool**|  | 
 **query** | **str**|  | [optional] 
 **type** | **str**|  | [optional] 
 **language** | **str**|  | [optional] 
 **index_type** | **str**|  | [optional] 
 **index_id** | **str**|  | [optional] 
 **page** | **int**|  | [optional] 
 **view** | [**SearchResultView**](.md)|  | [optional] 
 **filters** | [**List[FilterModel]**](FilterModel.md)|  | [optional] 

### Return type

[**JsonLdResourceDtoSearchResponseDto**](JsonLdResourceDtoSearchResponseDto.md)

### Authorization

[oauth2-user](../README.md#oauth2-user), [oauth2-client-credentials](../README.md#oauth2-client-credentials)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: text/plain, application/json, text/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**501** | Not Implemented |  -  |
**400** | Bad Request |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **search_suggestions**
> SuggestionDtoSearchResponseDto search_suggestions(query=query, size=size, type=type, language=language, include_bnodes=include_bnodes, property_name=property_name, top_level_search_query=top_level_search_query)

Search for resource suggestions based on the entered query.

Search for suggestions using:

- A `query`, which is any name, keyword, CTID, etc.

- A `size`, which is how many suggestions to return.

- A resource `type` (like `ceterms:Credential`). This defaults to all types if not included.

- A `language`, such as `en` (English), `fr` (French), or `es` (Spanish).

- Whether or not to `includeBnodes` in the results.

The response will have a list of resource results suggested for the query.

### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
from consumer_api_client.models.suggestion_dto_search_response_dto import (
    SuggestionDtoSearchResponseDto,
)
from consumer_api_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = consumer_api_client.Configuration(host="http://localhost")

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

configuration.access_token = os.environ["ACCESS_TOKEN"]

configuration.access_token = os.environ["ACCESS_TOKEN"]

# Enter a context with an instance of the API client
async with consumer_api_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = consumer_api_client.SearchApi(api_client)
    query = "query_example"  # str |  (optional)
    size = 10  # int |  (optional) (default to 10)
    type = "type_example"  # str |  (optional)
    language = "language_example"  # str |  (optional)
    include_bnodes = True  # bool |  (optional) (default to True)
    property_name = "property_name_example"  # str |  (optional)
    top_level_search_query = "top_level_search_query_example"  # str |  (optional)

    try:
        # Search for resource suggestions based on the entered query.
        api_response = await api_instance.search_suggestions(
            query=query,
            size=size,
            type=type,
            language=language,
            include_bnodes=include_bnodes,
            property_name=property_name,
            top_level_search_query=top_level_search_query,
        )
        print("The response of SearchApi->search_suggestions:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SearchApi->search_suggestions: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **query** | **str**|  | [optional] 
 **size** | **int**|  | [optional] [default to 10]
 **type** | **str**|  | [optional] 
 **language** | **str**|  | [optional] 
 **include_bnodes** | **bool**|  | [optional] [default to True]
 **property_name** | **str**|  | [optional] 
 **top_level_search_query** | **str**|  | [optional] 

### Return type

[**SuggestionDtoSearchResponseDto**](SuggestionDtoSearchResponseDto.md)

### Authorization

[oauth2-user](../README.md#oauth2-user), [oauth2-client-credentials](../README.md#oauth2-client-credentials)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: text/plain, application/json, text/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**400** | Bad Request |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

