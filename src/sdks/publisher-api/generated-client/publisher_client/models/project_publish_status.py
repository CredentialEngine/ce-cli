from enum import StrEnum


class ProjectPublishStatus(StrEnum):
    NOTPUBLISHED = "NotPublished"
    PUBLISHED = "Published"
    PUBLISHFAILED = "PublishFailed"
    PUBLISHING = "Publishing"

    def __str__(self) -> str:
        return str(self.value)
