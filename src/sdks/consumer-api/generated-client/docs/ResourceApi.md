# consumer_api_client.ResourceApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**resource_get_inverse_relationships_by_ctid**](ResourceApi.md#resource_get_inverse_relationships_by_ctid) | **GET** /resources/inverse | Fetch inverse relations for a resource
[**resource_get_resource_by_bnode_guid**](ResourceApi.md#resource_get_resource_by_bnode_guid) | **GET** /resources/bnodes/{guid} | Fetch resource data for a bnode.
[**resource_get_resource_by_ctid**](ResourceApi.md#resource_get_resource_by_ctid) | **GET** /resources/{ctid} | Fetch a resource by providing its CTID.
[**resource_get_resource_statistics**](ResourceApi.md#resource_get_resource_statistics) | **GET** /resources/statistics | Fetch statistics about the different classes in the registry.
[**resource_get_resources_by_bnode_guid_list**](ResourceApi.md#resource_get_resources_by_bnode_guid_list) | **POST** /resources/bnodes/bulkGet | Provide a list of bnode URIs and retrieve all the resources.
[**resource_get_resources_by_ctid_list**](ResourceApi.md#resource_get_resources_by_ctid_list) | **POST** /resources/bulkGet | Provide a list of CTIDs and retrieve all the resources.


# **resource_get_inverse_relationships_by_ctid**
> List[ResourceIdDto] resource_get_inverse_relationships_by_ctid(source_url=source_url)

Fetch inverse relations for a resource

Provide a CTID.
The response will have a list of CTIDs belonging to any inverse relations, which should be anythingthat references the resource with the provided CTID externally.

### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
from consumer_api_client.models.resource_id_dto import ResourceIdDto
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
    api_instance = consumer_api_client.ResourceApi(api_client)
    source_url = "source_url_example"  # str |  (optional)

    try:
        # Fetch inverse relations for a resource
        api_response = await api_instance.resource_get_inverse_relationships_by_ctid(
            source_url=source_url
        )
        print(
            "The response of ResourceApi->resource_get_inverse_relationships_by_ctid:\n"
        )
        pprint(api_response)
    except Exception as e:
        print(
            "Exception when calling ResourceApi->resource_get_inverse_relationships_by_ctid: %s\n"
            % e
        )
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **source_url** | **str**|  | [optional] 

### Return type

[**List[ResourceIdDto]**](ResourceIdDto.md)

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
**404** | Not Found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **resource_get_resource_by_bnode_guid**
> JsonLdResourceDto resource_get_resource_by_bnode_guid(guid)

Fetch resource data for a bnode.

Provide the full URI for the bnode, such as `d58fa54b-6582-48cd-8a72-720f194e18b5`

The response will return a result with the full resource.

### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
from consumer_api_client.models.json_ld_resource_dto import JsonLdResourceDto
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
    api_instance = consumer_api_client.ResourceApi(api_client)
    guid = UUID("38400000-8cf0-11bd-b23e-10b96e4ef00d")  # UUID |

    try:
        # Fetch resource data for a bnode.
        api_response = await api_instance.resource_get_resource_by_bnode_guid(guid)
        print("The response of ResourceApi->resource_get_resource_by_bnode_guid:\n")
        pprint(api_response)
    except Exception as e:
        print(
            "Exception when calling ResourceApi->resource_get_resource_by_bnode_guid: %s\n"
            % e
        )
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **guid** | **UUID**|  | 

### Return type

[**JsonLdResourceDto**](JsonLdResourceDto.md)

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

# **resource_get_resource_by_ctid**
> JsonLdResourceDto resource_get_resource_by_ctid(ctid)

Fetch a resource by providing its CTID.

Make a request with a CTID.
It will return a result with the full resource.



### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
from consumer_api_client.models.json_ld_resource_dto import JsonLdResourceDto
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
    api_instance = consumer_api_client.ResourceApi(api_client)
    ctid = "ce-00000000-0000-0000-0000-000000000000"  # str |

    try:
        # Fetch a resource by providing its CTID.
        api_response = await api_instance.resource_get_resource_by_ctid(ctid)
        print("The response of ResourceApi->resource_get_resource_by_ctid:\n")
        pprint(api_response)
    except Exception as e:
        print(
            "Exception when calling ResourceApi->resource_get_resource_by_ctid: %s\n"
            % e
        )
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **ctid** | **str**|  | 

### Return type

[**JsonLdResourceDto**](JsonLdResourceDto.md)

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

# **resource_get_resource_statistics**
> List[ResourceTypeStatistic] resource_get_resource_statistics(types=types)

Fetch statistics about the different classes in the registry.

Provide a list of class types, such as `ceterms:Credential` and `ceterms:Organization`.

For each class, the response will provide a class label, type, the count of resources in that class (both with and without children), and the same info for its children if the class has children.

### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
from consumer_api_client.models.resource_type_statistic import ResourceTypeStatistic
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
    api_instance = consumer_api_client.ResourceApi(api_client)
    types = ["types_example"]  # List[str] |  (optional)

    try:
        # Fetch statistics about the different classes in the registry.
        api_response = await api_instance.resource_get_resource_statistics(types=types)
        print("The response of ResourceApi->resource_get_resource_statistics:\n")
        pprint(api_response)
    except Exception as e:
        print(
            "Exception when calling ResourceApi->resource_get_resource_statistics: %s\n"
            % e
        )
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **types** | [**List[str]**](str.md)|  | [optional] 

### Return type

[**List[ResourceTypeStatistic]**](ResourceTypeStatistic.md)

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

# **resource_get_resources_by_bnode_guid_list**
> List[JsonLdResourceDto] resource_get_resources_by_bnode_guid_list(request_body=request_body)

Provide a list of bnode URIs and retrieve all the resources.

Provide a list of bnodes like:

- `["d58fa54b-6582-48cd-8a72-720f194e18b5", "e0a4fc18-dcc8-4f69-abaa-585240420882"]`

The response will have a list of resource results from each bnode URI in the query.

There is a max of 50 URIs allowed per request.

### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
from consumer_api_client.models.json_ld_resource_dto import JsonLdResourceDto
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
    api_instance = consumer_api_client.ResourceApi(api_client)
    request_body = None  # List[UUID] |  (optional)

    try:
        # Provide a list of bnode URIs and retrieve all the resources.
        api_response = await api_instance.resource_get_resources_by_bnode_guid_list(
            request_body=request_body
        )
        print(
            "The response of ResourceApi->resource_get_resources_by_bnode_guid_list:\n"
        )
        pprint(api_response)
    except Exception as e:
        print(
            "Exception when calling ResourceApi->resource_get_resources_by_bnode_guid_list: %s\n"
            % e
        )
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **request_body** | [**List[UUID]**](UUID.md)|  | [optional] 

### Return type

[**List[JsonLdResourceDto]**](JsonLdResourceDto.md)

### Authorization

[oauth2-user](../README.md#oauth2-user), [oauth2-client-credentials](../README.md#oauth2-client-credentials)

### HTTP request headers

 - **Content-Type**: application/json, text/json, application/*+json
 - **Accept**: text/plain, application/json, text/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**400** | Bad Request |  -  |
**413** | Content Too Large |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **resource_get_resources_by_ctid_list**
> List[JsonLdResourceDto] resource_get_resources_by_ctid_list(request_body=request_body)

Provide a list of CTIDs and retrieve all the resources.

Provide a list of CTIDs like:

- `["ce-623b6352-95e8-41d9-a788-b046aa6076f6", "ce-1eb26510-de1c-40d6-b1e4-02c35317a628"]`

The response will have a list of resource results from each CTID in the query.

There is a max of 50 ctids allowed per request.

### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
from consumer_api_client.models.json_ld_resource_dto import JsonLdResourceDto
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
    api_instance = consumer_api_client.ResourceApi(api_client)
    request_body = ["request_body_example"]  # List[str] |  (optional)

    try:
        # Provide a list of CTIDs and retrieve all the resources.
        api_response = await api_instance.resource_get_resources_by_ctid_list(
            request_body=request_body
        )
        print("The response of ResourceApi->resource_get_resources_by_ctid_list:\n")
        pprint(api_response)
    except Exception as e:
        print(
            "Exception when calling ResourceApi->resource_get_resources_by_ctid_list: %s\n"
            % e
        )
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **request_body** | [**List[str]**](str.md)|  | [optional] 

### Return type

[**List[JsonLdResourceDto]**](JsonLdResourceDto.md)

### Authorization

[oauth2-user](../README.md#oauth2-user), [oauth2-client-credentials](../README.md#oauth2-client-credentials)

### HTTP request headers

 - **Content-Type**: application/json, text/json, application/*+json
 - **Accept**: text/plain, application/json, text/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**400** | Bad Request |  -  |
**413** | Content Too Large |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

