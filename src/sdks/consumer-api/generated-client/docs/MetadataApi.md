# consumer_api_client.MetadataApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**metadata_get_metadata_by_ctid**](MetadataApi.md#metadata_get_metadata_by_ctid) | **GET** /metadata/{ctid} | Fetch metadata for a resource by providing its CTID.
[**metadata_get_metadata_by_ctid_list**](MetadataApi.md#metadata_get_metadata_by_ctid_list) | **POST** /metadata/bulkGet | Provide a list of CTIDs and retrieve all the metadata.


# **metadata_get_metadata_by_ctid**
> MetadataDto metadata_get_metadata_by_ctid(ctid)

Fetch metadata for a resource by providing its CTID.

Make a request with a CTID.
The result will return with the metadata for that resource.



### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
from consumer_api_client.models.metadata_dto import MetadataDto
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
    api_instance = consumer_api_client.MetadataApi(api_client)
    ctid = "ce-00000000-0000-0000-0000-000000000000"  # str |

    try:
        # Fetch metadata for a resource by providing its CTID.
        api_response = await api_instance.metadata_get_metadata_by_ctid(ctid)
        print("The response of MetadataApi->metadata_get_metadata_by_ctid:\n")
        pprint(api_response)
    except Exception as e:
        print(
            "Exception when calling MetadataApi->metadata_get_metadata_by_ctid: %s\n"
            % e
        )
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **ctid** | **str**|  | 

### Return type

[**MetadataDto**](MetadataDto.md)

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

# **metadata_get_metadata_by_ctid_list**
> MetadataDto metadata_get_metadata_by_ctid_list(request_body=request_body)

Provide a list of CTIDs and retrieve all the metadata.

Provide a list of CTIDs like:

- `["ce-623b6352-95e8-41d9-a788-b046aa6076f6", "ce-1eb26510-de1c-40d6-b1e4-02c35317a628"]`

The response will have a list of metadata results from each CTID in the query.

There is a max of 50 ctids allowed per request.

### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
from consumer_api_client.models.metadata_dto import MetadataDto
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
    api_instance = consumer_api_client.MetadataApi(api_client)
    request_body = ["request_body_example"]  # List[str] |  (optional)

    try:
        # Provide a list of CTIDs and retrieve all the metadata.
        api_response = await api_instance.metadata_get_metadata_by_ctid_list(
            request_body=request_body
        )
        print("The response of MetadataApi->metadata_get_metadata_by_ctid_list:\n")
        pprint(api_response)
    except Exception as e:
        print(
            "Exception when calling MetadataApi->metadata_get_metadata_by_ctid_list: %s\n"
            % e
        )
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **request_body** | [**List[str]**](str.md)|  | [optional] 

### Return type

[**MetadataDto**](MetadataDto.md)

### Authorization

[oauth2-user](../README.md#oauth2-user), [oauth2-client-credentials](../README.md#oauth2-client-credentials)

### HTTP request headers

 - **Content-Type**: application/json, text/json, application/*+json
 - **Accept**: text/plain, application/json, text/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**404** | Not Found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

