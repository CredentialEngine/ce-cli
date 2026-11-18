from enum import StrEnum


class ProjectType(StrEnum):
    APIPUBLISHING = "ApiPublishing"
    BULKUPLOAD = "BulkUpload"
    RUBYREGISTRYSYNC = "RubyRegistrySync"

    def __str__(self) -> str:
        return str(self.value)
