# An enumeration of train record types
from enum import Enum

from .dpu_repo import DPURepository
from .base_record_repo import RecordRepository
# from backend.src.db.database_core import RepositoryRecordInvalid
from .eot_repo import EOTRepository
from .hot_repo import HOTRepository
from .db_core.exceptions import RepositoryError

"""
start of error: station_repo.py imports ..db.database_core.py BaseRepository

while loading BaseRepository from database_core.py; database_core.py file loads RecordTypes from 
.record_types.py
 
while loading record_types.py; record_types.py imports RecordRepository from base_record_repo.py

error occurs here: while loading base_record_repo.py, it imports BaseRepository from database_core.py; so circular dependency happens

database_core.py --> record_types.py
record_types.py --> base_record_repo.py
base_record_repo.py --> database_core.py BAD!  

"""
class RecordTypes(Enum):
    EOT = 1
    HOT = 2
    DPU = 3

class RepositoryRecordInvalid(RepositoryError):
    valid_types = list(RecordTypes._value2member_map_)
    default_message = f"Invalid record type provided! Value must be between {valid_types[0]} and {valid_types[-1]}."
    # super().__init__(f"Invalid record type provided: {value}! Must be between {valid_types[0]} and {valid_types[-1]}")
    
def has_value(value: int):
    return any(value == item.value for item in RecordTypes)

def get_record_repository(session, value: int | RecordTypes) -> RecordRepository:
    if not isinstance(value, (int, RecordTypes)):
        raise RepositoryRecordInvalid(value)
    
    match value:
        case RecordTypes.EOT | RecordTypes.EOT.value:
            return EOTRepository(session)
        case RecordTypes.HOT | RecordTypes.HOT.value:
            return HOTRepository(session)
        case RecordTypes.DPU | RecordTypes.DPU.value:
            return DPURepository(session)
        
    raise RepositoryRecordInvalid(value)


def get_all_repositories(session) -> list[RecordRepository]:
    valid_types = list(RecordTypes)
    return [get_record_repository(session, valid_types[i]) for i in range(0, len(valid_types) - 1)]
