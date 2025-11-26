# An enumeration of train record types
from enum import Enum
from api_strat import Record_API_Strategy
from dpu_strat import DPU_API_Strategy
from hot_strat import HOT_API_Strategy
from eot_strat import EOT_API_Strategy


class RecordTypes(Enum):
    EOT = 1
    HOT = 2
    DPU = 3
    
def has_value(value: int):
    return any(value == item.value for item in RecordTypes)

def get_strategy(value: int) -> Record_API_Strategy:
    match value:
        case RecordTypes.EOT.value:
            return EOT_API_Strategy()
        case RecordTypes.HOT.value:
            return HOT_API_Strategy()
        case RecordTypes.DPU.value:
            return DPU_API_Strategy()
    raise ValueError("Unknown type!")

def get_table_name(value: int) -> str:
    match value:
        case RecordTypes.EOT.value:
            return "EOTRecords"
        case RecordTypes.HOT.value:
            return "HOTRecords"
        case RecordTypes.DPU.value:
            return "DPURecords"
    raise ValueError("Unknown type!")