# consumer_api_client.SchemaApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**schema_get_labels**](SchemaApi.md#schema_get_labels) | **POST** /schemas/labels | Get human-readable labels for schema terms or nested schema property paths.
[**schema_get_nested_properties_of_class**](SchemaApi.md#schema_get_nested_properties_of_class) | **GET** /schemas/classes/{className}/properties/nested | Get raw nested schema property terms for a single class.
[**schema_get_properties_of_class**](SchemaApi.md#schema_get_properties_of_class) | **GET** /schemas/classes/{className}/properties | Get raw schema property terms for a single class.
[**schema_get_range_for_property_value**](SchemaApi.md#schema_get_range_for_property_value) | **GET** /schemas/properties/{propertyName}/rangeIncludes | Get value type for a given property
[**schema_get_range_for_property_values**](SchemaApi.md#schema_get_range_for_property_values) | **POST** /schemas/properties/rangeIncludes/bulk | Get value type for a given list of properties
[**schema_get_schema_properties**](SchemaApi.md#schema_get_schema_properties) | **GET** /schemas/properties | Get schema property paths
[**schema_get_sub_classes**](SchemaApi.md#schema_get_sub_classes) | **GET** /schemas/classes/{className}/subclasses | Get all subclasses for a class, including indirect descendants.
[**schema_get_values_for_property**](SchemaApi.md#schema_get_values_for_property) | **GET** /schemas/properties/{propertyName} | Get all values for a given property


# **schema_get_labels**
> Dict[str, str] schema_get_labels(language=language, request_body=request_body)

Get human-readable labels for schema terms or nested schema property paths.

For nested paths, each term is resolved individually and joined for display.
Example: 

`ceterms:ownedBy.ceterms:name` -> `Owned By` > `Name` 

Provide schema terms or dot-delimited property paths.
Provide preferred label language.
The response will have a dictionary of original term/path to human-readable label


### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
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
    api_instance = consumer_api_client.SchemaApi(api_client)
    language = "en"  # str |  (optional) (default to 'en')
    request_body = ["request_body_example"]  # List[str] |  (optional)

    try:
        # Get human-readable labels for schema terms or nested schema property paths.
        api_response = await api_instance.schema_get_labels(
            language=language, request_body=request_body
        )
        print("The response of SchemaApi->schema_get_labels:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SchemaApi->schema_get_labels: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **language** | **str**|  | [optional] [default to &#39;en&#39;]
 **request_body** | [**List[str]**](str.md)|  | [optional] 

### Return type

**Dict[str, str]**

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

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **schema_get_nested_properties_of_class**
> List[str] schema_get_nested_properties_of_class(class_name, depth=depth)

Get raw nested schema property terms for a single class.

Preserved for other possible schema-management uses.
Provide a class term or id.
Select the maximum nested expansion depth.
The response will have dot-delimited schema property terms.


### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
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
    api_instance = consumer_api_client.SchemaApi(api_client)
    class_name = "class_name_example"  # str |
    depth = 1  # int |  (optional) (default to 1)

    try:
        # Get raw nested schema property terms for a single class.
        api_response = await api_instance.schema_get_nested_properties_of_class(
            class_name, depth=depth
        )
        print("The response of SchemaApi->schema_get_nested_properties_of_class:\n")
        pprint(api_response)
    except Exception as e:
        print(
            "Exception when calling SchemaApi->schema_get_nested_properties_of_class: %s\n"
            % e
        )
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **class_name** | **str**|  | 
 **depth** | **int**|  | [optional] [default to 1]

### Return type

**List[str]**

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

# **schema_get_properties_of_class**
> List[str] schema_get_properties_of_class(class_name, include_base_classes=include_base_classes)

Get raw schema property terms for a single class.

Provide a class term or id.
Select whether to include inherited base class properties.
The response will have the schema property terms.


### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
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
    api_instance = consumer_api_client.SchemaApi(api_client)
    class_name = "class_name_example"  # str |
    include_base_classes = True  # bool |  (optional) (default to True)

    try:
        # Get raw schema property terms for a single class.
        api_response = await api_instance.schema_get_properties_of_class(
            class_name, include_base_classes=include_base_classes
        )
        print("The response of SchemaApi->schema_get_properties_of_class:\n")
        pprint(api_response)
    except Exception as e:
        print(
            "Exception when calling SchemaApi->schema_get_properties_of_class: %s\n" % e
        )
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **class_name** | **str**|  | 
 **include_base_classes** | **bool**|  | [optional] [default to True]

### Return type

**List[str]**

### Authorization

[oauth2-user](../README.md#oauth2-user), [oauth2-client-credentials](../README.md#oauth2-client-credentials)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: text/plain, application/json, text/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **schema_get_range_for_property_value**
> List[str] schema_get_range_for_property_value(property_name)

Get value type for a given property

Provide a term or id.
The response will provide the types of the property value.


### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
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
    api_instance = consumer_api_client.SchemaApi(api_client)
    property_name = "property_name_example"  # str |

    try:
        # Get value type for a given property
        api_response = await api_instance.schema_get_range_for_property_value(
            property_name
        )
        print("The response of SchemaApi->schema_get_range_for_property_value:\n")
        pprint(api_response)
    except Exception as e:
        print(
            "Exception when calling SchemaApi->schema_get_range_for_property_value: %s\n"
            % e
        )
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **property_name** | **str**|  | 

### Return type

**List[str]**

### Authorization

[oauth2-user](../README.md#oauth2-user), [oauth2-client-credentials](../README.md#oauth2-client-credentials)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: text/plain, application/json, text/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **schema_get_range_for_property_values**
> Dict[str, List[str]] schema_get_range_for_property_values(request_body=request_body)

Get value type for a given list of properties

Provide a list of properties. 
The response will provide a dictionary of types for each property.


### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
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
    api_instance = consumer_api_client.SchemaApi(api_client)
    request_body = ["request_body_example"]  # List[str] |  (optional)

    try:
        # Get value type for a given list of properties
        api_response = await api_instance.schema_get_range_for_property_values(
            request_body=request_body
        )
        print("The response of SchemaApi->schema_get_range_for_property_values:\n")
        pprint(api_response)
    except Exception as e:
        print(
            "Exception when calling SchemaApi->schema_get_range_for_property_values: %s\n"
            % e
        )
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **request_body** | [**List[str]**](str.md)|  | [optional] 

### Return type

**Dict[str, List[str]]**

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

# **schema_get_schema_properties**
> Dict[str, List[str]] schema_get_schema_properties(class_name=class_name, depth=depth)

Get schema property paths

If `className` is provided, returns properties for that class only.
If `className` is omitted, returns properties for all main search types.

Provide `depth` for maximum nested expansion depth.

0 returns only direct and inherited properties.

1 returns direct, inherited, and one nested level.

The response will contain graph data for that resource and the resources that are 
connected to it, to the level of depth that is provided. 
Returned values are Elasticsearch dot-paths, for example: 

- ceterms:name
- ceterms:ownedBy.ceterms:name
- ceterms:ownedBy.ceterms:description


### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
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
    api_instance = consumer_api_client.SchemaApi(api_client)
    class_name = "class_name_example"  # str |  (optional)
    depth = 1  # int |  (optional) (default to 1)

    try:
        # Get schema property paths
        api_response = await api_instance.schema_get_schema_properties(
            class_name=class_name, depth=depth
        )
        print("The response of SchemaApi->schema_get_schema_properties:\n")
        pprint(api_response)
    except Exception as e:
        print(
            "Exception when calling SchemaApi->schema_get_schema_properties: %s\n" % e
        )
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **class_name** | **str**|  | [optional] 
 **depth** | **int**|  | [optional] [default to 1]

### Return type

**Dict[str, List[str]]**

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

# **schema_get_sub_classes**
> List[str] schema_get_sub_classes(class_name)

Get all subclasses for a class, including indirect descendants.

Preserved for other possible schema-management uses.
Provide a base class term or id.
The response will have the subclass terms.


### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
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
    api_instance = consumer_api_client.SchemaApi(api_client)
    class_name = "class_name_example"  # str |

    try:
        # Get all subclasses for a class, including indirect descendants.
        api_response = await api_instance.schema_get_sub_classes(class_name)
        print("The response of SchemaApi->schema_get_sub_classes:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SchemaApi->schema_get_sub_classes: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **class_name** | **str**|  | 

### Return type

**List[str]**

### Authorization

[oauth2-user](../README.md#oauth2-user), [oauth2-client-credentials](../README.md#oauth2-client-credentials)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: text/plain, application/json, text/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **schema_get_values_for_property**
> List[str] schema_get_values_for_property(property_name)

Get all values for a given property

Provide a term or id.
The response will provide a list of the value options for the property.
If there are no value options, the response will provide an empty list.


### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
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
    api_instance = consumer_api_client.SchemaApi(api_client)
    property_name = "property_name_example"  # str |

    try:
        # Get all values for a given property
        api_response = await api_instance.schema_get_values_for_property(property_name)
        print("The response of SchemaApi->schema_get_values_for_property:\n")
        pprint(api_response)
    except Exception as e:
        print(
            "Exception when calling SchemaApi->schema_get_values_for_property: %s\n" % e
        )
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **property_name** | **str**|  | 

### Return type

**List[str]**

### Authorization

[oauth2-user](../README.md#oauth2-user), [oauth2-client-credentials](../README.md#oauth2-client-credentials)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: text/plain, application/json, text/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

