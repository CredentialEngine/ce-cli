# consumer_api_client.WorkflowEventsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**workflow_events_ceops**](WorkflowEventsApi.md#workflow_events_ceops) | **POST** /workflow-events/ceops | 


# **workflow_events_ceops**
> workflow_events_ceops(workflow_event=workflow_event)

### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
from consumer_api_client.models.workflow_event import WorkflowEvent
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
    api_instance = consumer_api_client.WorkflowEventsApi(api_client)
    workflow_event = consumer_api_client.WorkflowEvent()  # WorkflowEvent |  (optional)

    try:
        await api_instance.workflow_events_ceops(workflow_event=workflow_event)
    except Exception as e:
        print(
            "Exception when calling WorkflowEventsApi->workflow_events_ceops: %s\n" % e
        )
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **workflow_event** | [**WorkflowEvent**](WorkflowEvent.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[oauth2-user](../README.md#oauth2-user), [oauth2-client-credentials](../README.md#oauth2-client-credentials)

### HTTP request headers

 - **Content-Type**: application/json, text/json, application/*+json
 - **Accept**: Not defined

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

