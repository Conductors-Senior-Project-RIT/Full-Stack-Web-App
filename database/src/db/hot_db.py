"""
HOT database layer 

This module handles all database CRUD operations for HOT records
"""

from typing import Any
from trackSense_db_commands import run_get_cmd, run_exec_cmd

RESULTS_NUM = 250
# below is train_history.py related
def get_hot_data_by_train_id(id: int, page: int) -> list[tuple[Any,...]] | None:
    sql = """
            SELECT HOTRecords.id, date_rec, stat.station_name, symbol_id, unit_addr, command, checkbits, parity, verified FROM HOTRecords
            INNER JOIN Stations as stat on station_recorded = stat.id
            WHERE HOTRecords.id = %(id)s
            LIMIT %(results_num)s OFFSET %(offset)s * %(results_num)s
            """
    sql_args = {"id": id, "results_num": RESULTS_NUM, "offset": page - 1}
    resp = run_get_cmd(sql, sql_args)

def create_hot_record(args: dict[str, Any], datetime_string: str) -> None:
    """
    TODO: Namespace is the type for args for post methods in train_history... look more into this
    TODO: run_exec_cmd returns none always... think of what to return lol
    """
    recovery_request = True # what is this lol

    sql_args = {
        "date": args["date_rec"],
        "station": args["station_id"],
        "frame_sync": args["frame_sync"],
        "command": args["command"],
        "checkbits": args["checkbits"],
        "parity": args["parity"],
        "unit_addr": args["unit_addr"],
    }

    if args["date_rec"] is None:
        sql_args["date"] = datetime_string
        recovery_request = False

    sql = """
            INSERT INTO HOTRecords (date_rec, station_recorded, frame_sync, unit_addr, command, checkbits, parity) VALUES
            (%(date)s, %(station)s, %(frame_sync)s, %(unit_addr)s, %(command)s, %(checkbits)s, %(parity)s)
        """
    
    return run_exec_cmd(sql, sql_args), recovery_request

def add_new_hot_pin(unit_addr: int, hot_id: int) -> bool:
    update_args = {"id": hot_id, "unit_addr": unit_addr}
    sql_update = """
                UPDATE HOTRecords
                SET most_recent = false
                WHERE id != %(id)s and unit_addr = %(unit_addr)s and most_recent = true
                """
    run_exec_cmd(sql_update, update_args)

def get_newest_hot_id(unit_addr: str) -> int | None:
    sql_hot_id = """
        SELECT id FROM HOTRecords
        WHERE unit_addr = %(unit_addr)s
    """
    sql_hot_id_args = {"unit_addr": unit_addr}
    resp_hot_id = run_get_cmd(sql_hot_id, sql_hot_id_args)
    return resp_hot_id[len(resp_hot_id) - 1][0]

    return None

def check_for_hot_symbol(unit_addr: str) -> int | None:
    sql_hot_symb = """
    SELECT symbol_id FROM HOTRecords 
    WHERE unit_addr = %(unit_addr)s and most_recent = True
    """
    sql_param = {"unit_addr": unit_addr}

    resp = run_get_cmd(sql_hot_symb, sql_param)
    if len(resp) == 1:
        return resp[0][0]
    
    return None

def check_for_hot_engine(unit_addr: str) -> int | None:
    sql_hot_engi = """
    SELECT engine_num FROM HOTRecords
    WHERE unit_addr = %(unit_addr)s and most_recent = True
    """
    sql_param = {"unit_addr": unit_addr}

    resp = run_get_cmd(sql_hot_engi, sql_param)
    if len(resp) == 1:
        return resp[0][0]
    
    return None

def attempt_auto_fill_hot_info_no_symbol(symbol_id: int, hot_id: int) -> bool:
    # id = self.get_newest_eot_id(unit_addr)
    sql_update = """
    UPDATE HOTRecords
    SET symbol_id = %(symb_id)s
    WHERE id = %(id)s
    """
    update_param = {"symb_id": symbol_id, "id": hot_id}

    resp = run_exec_cmd(sql_update, update_param)

def attempt_auto_fill_hot_info_no_engine(engine_id: int, hot_id: int) -> bool:
    sql_update = """
    UPDATE HOTRecords
    SET engine_num = %(engi_id)s
    WHERE id = %(id)s
    """
    update_param = {"engi_id": engine_id, "id": hot_id}

    resp = run_exec_cmd(sql_update, update_param)

def check_recent_hot_trains(unit_addr: str, station_id: int) -> bool:
    sql = """
        SELECT * FROM HOTRecords
        WHERE unit_addr = %(unit_address)s AND station_recorded = %(station_id)s AND date_rec >= NOW() - INTERVAL '10 minutes'
    """
    resp = run_get_cmd(
        sql, args={"unit_address": unit_addr, "station_id": station_id}
    )
    if resp:  # arbitrary number that will make this work
        return True
    
    return False

# below is for station_handler.py

def get_hot_train_data_by_station_id(station_id: str) -> list[tuple[Any,...]]:
    hot_records = run_get_cmd(
        "SELECT * FROM HOTRecords WHERE station_recorded = %s", (station_id,)
    )
    return hot_records

def get_hot_pin_info_by_station_id(station_id: int) -> list[tuple[Any,...]]:
    hot_records = run_get_cmd(
        "SELECT * FROM HOTRecords WHERE station_recorded = %s and most_recent = true",
        (station_id,),
    )
    return hot_records