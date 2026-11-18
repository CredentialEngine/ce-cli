from enum import StrEnum


class IterationStatus(StrEnum):
    CREATED = "Created"
    TRANSFORMED = "Transformed"
    TRANSFORMING = "Transforming"
    VALIDATED = "Validated"
    VALIDATING = "Validating"

    def __str__(self) -> str:
        return str(self.value)
