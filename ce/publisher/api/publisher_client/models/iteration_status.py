from enum import Enum

class IterationStatus(str, Enum):
    CREATED = "Created"
    TRANSFORMED = "Transformed"
    TRANSFORMING = "Transforming"
    VALIDATED = "Validated"
    VALIDATING = "Validating"

    def __str__(self) -> str:
        return str(self.value)
