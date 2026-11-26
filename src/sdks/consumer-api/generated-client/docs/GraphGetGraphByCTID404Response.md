# GraphGetGraphByCTID404Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** |  | 
**type** | **str** |  | [optional] 
**title** | **str** |  | [optional] 
**status** | **int** |  | [optional] 
**detail** | **str** |  | [optional] 
**instance** | **str** |  | [optional] 
**errors** | **Dict[str, List[str]]** |  | [optional] 

## Example

```python
from consumer_api_client.models.graph_get_graph_by_ctid404_response import (
    GraphGetGraphByCTID404Response,
)

# TODO update the JSON string below
json = "{}"
# create an instance of GraphGetGraphByCTID404Response from a JSON string
graph_get_graph_by_ctid404_response_instance = GraphGetGraphByCTID404Response.from_json(
    json
)
# print the JSON string representation of the object
print(GraphGetGraphByCTID404Response.to_json())

# convert the object into a dict
graph_get_graph_by_ctid404_response_dict = (
    graph_get_graph_by_ctid404_response_instance.to_dict()
)
# create an instance of GraphGetGraphByCTID404Response from a dict
graph_get_graph_by_ctid404_response_from_dict = (
    GraphGetGraphByCTID404Response.from_dict(graph_get_graph_by_ctid404_response_dict)
)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


