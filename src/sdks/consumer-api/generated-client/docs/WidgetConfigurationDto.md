# WidgetConfigurationDto


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**result** | **Dict[str, object]** |  | 

## Example

```python
from consumer_api_client.models.widget_configuration_dto import WidgetConfigurationDto

# TODO update the JSON string below
json = "{}"
# create an instance of WidgetConfigurationDto from a JSON string
widget_configuration_dto_instance = WidgetConfigurationDto.from_json(json)
# print the JSON string representation of the object
print(WidgetConfigurationDto.to_json())

# convert the object into a dict
widget_configuration_dto_dict = widget_configuration_dto_instance.to_dict()
# create an instance of WidgetConfigurationDto from a dict
widget_configuration_dto_from_dict = WidgetConfigurationDto.from_dict(
    widget_configuration_dto_dict
)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


