# An enumeration of train record types
from enum import Enum


class RecordTypes(Enum):
    EOT = 1
    HOT = 2
    DPU = 3
    
    @classmethod
    def has_value(value: int):
        return any(value == item.value for item in RecordTypes)