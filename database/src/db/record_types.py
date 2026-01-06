# An enumeration of train record types
from enum import Enum
from base_record_repo import RecordRepository
from database_status import RepositoryRecordInvalid
from eot_repo import EOTRepository
from hot_repo import HOTRepository


class RecordTypes(Enum):
    EOT = 1
    HOT = 2
    DPU = 3
    
def has_value(value: int):
    return any(value == item.value for item in RecordTypes)

def get_record_repository(value: int | RecordTypes) -> RecordRepository:
    if not isinstance(value, (int, RecordTypes)):
        raise RepositoryRecordInvalid(value)
    
    match value:
        case RecordTypes.EOT.value:
            return EOTRepository()
        case RecordTypes.HOT.value:
            return HOTRepository()
        # case RecordTypes.DPU.value:
        #     raise InvalidRecordError(value)
    raise RepositoryRecordInvalid(value)


def get_all_repositories() -> list[RecordRepository]:
    valid_types = list(RecordTypes._value2member_map_)
    return [get_record_repository(valid_types[i]) for i in range(valid_types[0], valid_types[len(valid_types)])]


