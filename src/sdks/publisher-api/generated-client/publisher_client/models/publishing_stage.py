from enum import StrEnum


class PublishingStage(StrEnum):
    CHANGESETAPPLICATION = "ChangesetApplication"
    CHANGESETGENERATION = "ChangesetGeneration"
    ELASTICSEARCHGRAPHSUPDATE = "ElasticsearchGraphsUpdate"
    ELASTICSEARCHMETADATAUPDATE = "ElasticsearchMetadataUpdate"
    ELASTICSEARCHRESOURCESUPDATE = "ElasticsearchResourcesUpdate"
    GRAPHDBUPDATE = "GraphDbUpdate"

    def __str__(self) -> str:
        return str(self.value)
