from enum import Enum

from database.src.service.strategy.record_types import RecordTypes


class ServiceStatusCode(Enum):
    PROCESS_SUCCESS = "Successfully Processed Results"
    INVALID_RECORD_TYPE = "Invalid Record Type"
    INVALID_RECORD_ID = "Invalid Record ID"
    UNKNOWN_ERROR = "Unknown Error"
    

class InvalidRecordError(Exception):
    def __init__(self, value):
        valid_types = list(RecordTypes._value2member_map_)
        super().__init__(f"Invalid record type provided: {value}! Must be between {valid_types[0]} and {valid_types[-1]}")

    