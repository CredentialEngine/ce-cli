from enum import Enum

class AuditEventTypes(str, Enum):
    COMPLETIONFAILED = "CompletionFailed"
    ITERATIONFILESADDED = "IterationFilesAdded"
    ITERATIONFILESDELETED = "IterationFilesDeleted"
    PROJECTABANDONED = "ProjectAbandoned"
    PROJECTAPPROVED = "ProjectApproved"
    PROJECTCOMPLETED = "ProjectCompleted"
    PROJECTCREATED = "ProjectCreated"
    PROJECTFINALIZED = "ProjectFinalized"
    PUBLISHINGCOMPLETED = "PublishingCompleted"
    PUBLISHINGSTAGECOMPLETED = "PublishingStageCompleted"
    PUBLISHINGSTAGEFAILED = "PublishingStageFailed"
    PUBLISHINGSTAGESTARTED = "PublishingStageStarted"
    PUBLISHINGSTARTED = "PublishingStarted"
    REVIEWERSADDED = "ReviewersAdded"
    REVIEWERSREMOVED = "ReviewersRemoved"
    TRANSFORMCOMPLETED = "TransformCompleted"
    TRANSFORMSTARTED = "TransformStarted"
    VALIDATIONCOMPLETED = "ValidationCompleted"
    VALIDATIONJOBCOMPLETED = "ValidationJobCompleted"
    VALIDATIONSTARTED = "ValidationStarted"

    def __str__(self) -> str:
        return str(self.value)
