from database.src.service.service_status import InvalidRecordError, ServiceStatusCode
from database.src.service.strategy import record_types
import database.src.db.base_record_repo as generic_db

# Temporary constant for number of results per page
RESULTS_NUM = 250


def get_train_history(record_type: int, record_id: int, page_num: int):
    try:
        record_strat = record_types.get_strategy(record_type)
        return record_strat.get_train_history(record_id, page_num, RESULTS_NUM)
    except InvalidRecordError as e:
        raise ValueError(str(e))
    except RuntimeError as e:
        raise RuntimeError(str(e))
    
    
def post_train_history(record_type: int, args: dict, datetime_str: str):
    try:
        record_strat = record_types.get_strategy(record_type)
        response, recovery_request = record_strat.post_train_record(args, datetime_str)
        
        # Do error handling etc.
        if not response:
            add_new_pin(record_strat.table_name, args["unit_addr"])
            
            has_notification = check_recent_notification(record_strat.table_name, args["unit_addr"], args["station_id"])
            
            if not has_notification and not recovery_request:
                # Send notification for HOT
                pass
        
    except InvalidRecordError as e:
        raise ValueError(str(e))
    except RuntimeError as e:
        raise RuntimeError(str(e))
    
    
def check_recent_notification(table_name: str, unit_addr: str, station_id: int) -> bool:
        return generic_db.check_recent_trains(table_name, unit_addr, station_id)
    
def add_new_pin(table_name: str, unit_addr: str):
    attempt_auto_fill(table_name, unit_addr)
    
    resp_id = generic_db.get_newest_record_id(table_name, unit_addr)
    result = generic_db.add_new_pin(table_name, resp_id, unit_addr)
    
def attempt_auto_fill(table_name: str, unit_addr: str):
    symb = generic_db.check_for_record_field(table_name, unit_addr, "symbol_id")
    engi = generic_db.check_for_record_field(table_name, unit_addr, "engine_num")
    record_id = generic_db.get_newest_record_id(table_name, unit_addr)
    
    if symb:
        resp = generic_db.update_record_field(table_name, record_id, symb, "symbol_id")
        
    if engi:
        resp = generic_db.update_record_field(table_name, unit_addr, engi, "engine_num")
    else:
        print("No engine number to update!")