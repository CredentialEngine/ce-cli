# consumer_api_client.GraphApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**graph_get_graph_by_ctid**](GraphApi.md#graph_get_graph_by_ctid) | **GET** /graphs/{ctid} | Allows you to fetch graphical data for a resource.


# **graph_get_graph_by_ctid**
> JsonLdGraphDto graph_get_graph_by_ctid(ctid, depth=depth)

Allows you to fetch graphical data for a resource.

Provide a CTID.
The response will contain graph data for that resource and the resources that are 
connected to it, to the level of depth that is provided. 



### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
from consumer_api_client.models.json_ld_graph_dto import JsonLdGraphDto
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
    api_instance = consumer_api_client.GraphApi(api_client)
    ctid = "ce-00000000-0000-0000-0000-000000000000"  # str |
    depth = 0  # int |  (optional) (default to 0)

    try:
        # Allows you to fetch graphical data for a resource.
        api_response = await api_instance.graph_get_graph_by_ctid(ctid, depth=depth)
        print("The response of GraphApi->graph_get_graph_by_ctid:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling GraphApi->graph_get_graph_by_ctid: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **ctid** | **str**|  | 
 **depth** | **int**|  | [optional] [default to 0]

### Return type

[**JsonLdGraphDto**](JsonLdGraphDto.md)

### Authorization

[oauth2-user](../README.md#oauth2-user), [oauth2-client-credentials](../README.md#oauth2-client-credentials)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: text/plain, application/json, text/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**404** | Not Found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

