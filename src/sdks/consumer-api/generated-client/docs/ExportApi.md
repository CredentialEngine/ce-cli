# consumer_api_client.ExportApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**export_create_search_export**](ExportApi.md#export_create_search_export) | **POST** /exports/search | Create a Registry search export.
[**export_download**](ExportApi.md#export_download) | **GET** /exports/files/{nonce}/{fileName} | Redeem a one-time Registry export download URL.
[**export_get_downloads**](ExportApi.md#export_get_downloads) | **GET** /exports/downloads/{dateOrLatest} | Get Registry export downloads.
[**export_get_search_export**](ExportApi.md#export_get_search_export) | **GET** /exports/search/{jobId} | Get Registry search export status.
[**export_get_search_export_downloads**](ExportApi.md#export_get_search_export_downloads) | **GET** /exports/search/{jobId}/downloads | Get Registry search export downloads.


# **export_create_search_export**
> export_create_search_export(create_search_export_request=create_search_export_request)

Create a Registry search export.

Starts an asynchronous export job for Registry resources matching the submitted search query. Supports authenticated users and authorized service clients. The completed export contains a ZIP archive and manifest.

### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
from consumer_api_client.models.create_search_export_request import (
    CreateSearchExportRequest,
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
    api_instance = consumer_api_client.ExportApi(api_client)
    create_search_export_request = (
        consumer_api_client.CreateSearchExportRequest()
    )  # CreateSearchExportRequest |  (optional)

    try:
        # Create a Registry search export.
        await api_instance.export_create_search_export(
            create_search_export_request=create_search_export_request
        )
    except Exception as e:
        print("Exception when calling ExportApi->export_create_search_export: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_search_export_request** | [**CreateSearchExportRequest**](CreateSearchExportRequest.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[oauth2-user](../README.md#oauth2-user), [oauth2-client-credentials](../README.md#oauth2-client-credentials)

### HTTP request headers

 - **Content-Type**: application/json, text/json, application/*+json
 - **Accept**: text/plain, application/json, text/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**202** | Accepted |  -  |
**401** | Unauthorized |  -  |
**400** | Bad Request |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **export_download**
> export_download(nonce, file_name)

Redeem a one-time Registry export download URL.

Atomically consumes the Redis-backed nonce and redirects the caller to a short-lived signed Blob Storage URL. The same endpoint is used for full Registry exports and search exports.

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
    api_instance = consumer_api_client.ExportApi(api_client)
    nonce = "nonce_example"  # str |
    file_name = "file_name_example"  # str |

    try:
        # Redeem a one-time Registry export download URL.
        await api_instance.export_download(nonce, file_name)
    except Exception as e:
        print("Exception when calling ExportApi->export_download: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **nonce** | **str**|  | 
 **file_name** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[oauth2-user](../README.md#oauth2-user), [oauth2-client-credentials](../README.md#oauth2-client-credentials)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: text/plain, application/json, text/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**302** | Found |  -  |
**404** | Not Found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **export_get_downloads**
> ExportDownloadsResponseDto export_get_downloads(date_or_latest)

Get Registry export downloads.

Returns the latest completed Registry export, or the newest completed export on the requested UTC date. An export is considered available only when its manifest.json is present. Use `latest` or a date in yyyy-MM-dd format.

### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
from consumer_api_client.models.export_downloads_response_dto import (
    ExportDownloadsResponseDto,
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
    api_instance = consumer_api_client.ExportApi(api_client)
    date_or_latest = "latest"  # str |  (default to 'latest')

    try:
        # Get Registry export downloads.
        api_response = await api_instance.export_get_downloads(date_or_latest)
        print("The response of ExportApi->export_get_downloads:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ExportApi->export_get_downloads: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **date_or_latest** | **str**|  | [default to &#39;latest&#39;]

### Return type

[**ExportDownloadsResponseDto**](ExportDownloadsResponseDto.md)

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

# **export_get_search_export**
> export_get_search_export(job_id)

Get Registry search export status.

Returns the current status and metadata for an asynchronous Registry search export job. Only the original requester can access the job.

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
    api_instance = consumer_api_client.ExportApi(api_client)
    job_id = "job_id_example"  # str |

    try:
        # Get Registry search export status.
        await api_instance.export_get_search_export(job_id)
    except Exception as e:
        print("Exception when calling ExportApi->export_get_search_export: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **job_id** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[oauth2-user](../README.md#oauth2-user), [oauth2-client-credentials](../README.md#oauth2-client-credentials)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: text/plain, application/json, text/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**401** | Unauthorized |  -  |
**404** | Not Found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **export_get_search_export_downloads**
> List[ExportFileDto] export_get_search_export_downloads(job_id)

Get Registry search export downloads.

Returns one-time download URLs for all ZIP archives in the completed search export. Only the original requester can access the download.

### Example

* OAuth Authentication (oauth2-user):
* OAuth Authentication (oauth2-client-credentials):

```python
import consumer_api_client
from consumer_api_client.models.export_file_dto import ExportFileDto
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
    api_instance = consumer_api_client.ExportApi(api_client)
    job_id = "job_id_example"  # str |

    try:
        # Get Registry search export downloads.
        api_response = await api_instance.export_get_search_export_downloads(job_id)
        print("The response of ExportApi->export_get_search_export_downloads:\n")
        pprint(api_response)
    except Exception as e:
        print(
            "Exception when calling ExportApi->export_get_search_export_downloads: %s\n"
            % e
        )
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **job_id** | **str**|  | 

### Return type

[**List[ExportFileDto]**](ExportFileDto.md)

### Authorization

[oauth2-user](../README.md#oauth2-user), [oauth2-client-credentials](../README.md#oauth2-client-credentials)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: text/plain, application/json, text/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | OK |  -  |
**401** | Unauthorized |  -  |
**404** | Not Found |  -  |
**409** | Conflict |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

