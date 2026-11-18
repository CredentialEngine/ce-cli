from enum import StrEnum


class ProjectStatus(StrEnum):
    ABANDONED = "Abandoned"
    ACTIVE = "Active"
    APPROVED = "Approved"
    COMPLETED = "Completed"

    def __str__(self) -> str:
        return str(self.value)
