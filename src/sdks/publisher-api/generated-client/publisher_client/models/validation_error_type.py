from enum import StrEnum


class ValidationErrorType(StrEnum):
    CSVSTRUCTURE = "CsvStructure"
    CTIDREFERENCE = "CtidReference"
    JSONLD = "JsonLd"
    NONE = "None"
    SPELLCHECK = "SpellCheck"
    URL = "Url"
    WHITESPACE = "Whitespace"

    def __str__(self) -> str:
        return str(self.value)
