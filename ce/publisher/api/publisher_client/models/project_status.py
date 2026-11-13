from enum import Enum

class ProjectStatus(str, Enum):
    ABANDONED = "Abandoned"
    ACTIVE = "Active"
    APPROVED = "Approved"
    COMPLETED = "Completed"

    def __str__(self) -> str:
        return str(self.value)
