# An enumeration of train record types
from enum import Enum
from database.src.db.base_record_repo import RecordRepository
from database.src.db.eot_repo import EOTRepository
from database.src.db.hot_repo import HOTRepository
from database.src.service.service_status import InvalidRecordError


class RecordTypes(Enum):
    EOT = 1
    HOT = 2
    DPU = 3
    
def has_value(value: int):
    return any(value == item.value for item in RecordTypes)

def get_record_repository(value: int | RecordTypes) -> RecordRepository:
    match value:
        case RecordTypes.EOT.value:
            return EOTRepository()
        case RecordTypes.HOT.value:
            return HOTRepository()
        # case RecordTypes.DPU.value:
        #     raise InvalidRecordError(value)
    raise InvalidRecordError(value)