from enum import Enum

class ProjectPublishStatus(str, Enum):
    NOTPUBLISHED = "NotPublished"
    PUBLISHED = "Published"
    PUBLISHFAILED = "PublishFailed"
    PUBLISHING = "Publishing"

    def __str__(self) -> str:
        return str(self.value)
