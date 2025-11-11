"""
EOT database layer 

This module handles all database CRUD operations for EOT records
"""

from typing import Optional, Any
from trackSense_db_commands import run_get_cmd, run_exec_cmd

RESULTS_NUM = 250
        
def get_total_count_of_eot_records() -> int:
    "TODO: integrate this function to replace sql queries in train_history.py's def get_eot()"

    return run_get_cmd("SELECT COUNT(*) FROM EOTRecords")
    
def get_eot_data_by_train_id(id: int, page: int) -> Optional[list[tuple[Any,...]]]:
    """
    TODO: integrate this function to replace sql queries in train_history.py's def get_eot() 
    Returns either nothing or eot records for a specific train id
    "id": The id of a train record to retrieve.
    "page": The page of records to return.

    Returns:
        Either none or a list of tuples containing eot records for a specific train id
   
    What it will replace: 
        def get_eot(self, id: int, page: int) -> Response in train_history.py
    """

    sql = """
        SELECT EOTRecords.id, date_rec, stat.station_name, symbol_id, unit_addr, brake_pressure, motion, marker_light, turbine, battery_cond, battery_charge, arm_status, signal_strength, verified 
        FROM EOTRecords
        INNER JOIN Stations as stat on station_recorded = stat.id
        WHERE EOTRecords.id = %(id)s ORDER BY EOTRecords.id Desc" if id == RecordTypes.EOT.value else "ORDER BY date_rec DESC
        LIMIT %(results_num)s OFFSET %(offset)s * %(results_num)s
    """
    
    sql_args = {"results_num": RESULTS_NUM, "offset": page - 1, "id": id}

    return run_get_cmd(sql, sql_args)

