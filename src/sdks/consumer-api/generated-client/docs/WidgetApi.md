# consumer_api_client.WidgetApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**widget_get_widget_by_id_or_alias**](WidgetApi.md#widget_get_widget_by_id_or_alias) | **GET** /widgets/{widgetIdentifier} | Fetch widget configuration by widget identifier.


# **widget_get_widget_by_id_or_alias**
> WidgetConfigurationDto widget_get_widget_by_id_or_alias(widget_identifier)

Fetch widget configuration by widget identifier.

Make a request with a widget identifier.
The result will return with the configuration for that widget.



### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
from consumer_api_client.models.widget_configuration_dto import WidgetConfigurationDto
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
    api_instance = consumer_api_client.WidgetApi(api_client)
    widget_identifier = "widget_identifier_example"  # str |

    try:
        # Fetch widget configuration by widget identifier.
        api_response = await api_instance.widget_get_widget_by_id_or_alias(
            widget_identifier
        )
        print("The response of WidgetApi->widget_get_widget_by_id_or_alias:\n")
        pprint(api_response)
    except Exception as e:
        print(
            "Exception when calling WidgetApi->widget_get_widget_by_id_or_alias: %s\n"
            % e
        )
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **widget_identifier** | **str**|  | 

### Return type

[**WidgetConfigurationDto**](WidgetConfigurationDto.md)

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
**400** | Bad Request |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

