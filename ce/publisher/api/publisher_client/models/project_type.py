from enum import Enum


class ProjectType(str, Enum):
    APIPUBLISHING = "ApiPublishing"
    BULKUPLOAD = "BulkUpload"
    RUBYREGISTRYSYNC = "RubyRegistrySync"

    def __str__(self) -> str:
        return str(self.value)
