from enum import Enum

class PublishingStage(str, Enum):
    CHANGESETAPPLICATION = "ChangesetApplication"
    CHANGESETGENERATION = "ChangesetGeneration"
    ELASTICSEARCHGRAPHSUPDATE = "ElasticsearchGraphsUpdate"
    ELASTICSEARCHMETADATAUPDATE = "ElasticsearchMetadataUpdate"
    ELASTICSEARCHRESOURCESUPDATE = "ElasticsearchResourcesUpdate"
    GRAPHDBUPDATE = "GraphDbUpdate"

    def __str__(self) -> str:
        return str(self.value)
