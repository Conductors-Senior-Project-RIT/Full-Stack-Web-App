"""
EOT database layer 

This module handles all database CRUD operations for EOT records
"""

from typing import Optional, Any, Tuple
from psycopg2 import Cursor
from trackSense_db_commands import run_get_cmd, run_exec_cmd

RESULTS_NUM = 250
        
def get_total_count_of_eot_records() -> int:
    "TODO: integrate this function to replace sql queries in train_history.py's def get_eot()"

    try:
        response = run_get_cmd("SELECT COUNT(*) FROM EOTRecords")

        if response:
            return response[0][0]
        
        return -1
    except Exception as e:
        print(f"Error getting EOT record count: {e}")
        return -1
    
def get_eot_data_by_train_id(id: int, page: int) -> Optional[list[tuple[Any,...]]]:
    """
    TODO: integrate this function to replace sql queries in train_history.py's def get_eot() 
    TODO: how to go about error handling? DB errors like connceting issues, etc. | handling empty results frmo query | tpye validation and ranges of values allowed? 
    TODO: what is symbol_id for a train, is it it's unique identifier?
    
    Returns either nothing or eot records for a specific train id
    "id": The id of an eot train record to retrieve.
    "page": The page of records to return.

    Returns:
        Either none or a list of tuples containing eot records for a specific train id
   
    What it will replace: 
        def get_eot(self, id: int, page: int) -> Response in train_history.py
    """

    if not isinstance(id, int):
        raise ValueError(f"id ({id}) is not an integer")
    
    if not isinstance(page, int):
        raise ValueError(f"page ({page}), are not integer")

    try:
        sql = """
            SELECT EOTRecords.id, date_rec, stat.station_name, symbol_id, unit_addr, brake_pressure, motion, marker_light, turbine, battery_cond, battery_charge, arm_status, signal_strength, verified 
            FROM EOTRecords
            INNER JOIN Stations as stat on station_recorded = stat.id
            WHERE EOTRecords.id = %(id)s ORDER BY EOTRecords.id Desc" if id == RecordTypes.EOT.value else "ORDER BY date_rec DESC
            LIMIT %(results_num)s OFFSET %(offset)s * %(results_num)s
        """
        sql_args = {"results_num": RESULTS_NUM, "offset": page - 1, "id": id}
        data = run_get_cmd(sql, sql_args)

        if data:
            return data
    
        return None
    
    except Exception as e:
        print(f"Database error retrieving EOT data for symbol_id ({id}) and page ({page}): {e}")
        return None

def create_eot_record(args: dict[str, Any], datetime_string: str) -> Cursor:  #post_eot()
    """
    TODO: integrate this function to replace sql queries in train_history.py's post_eot() | train_history post() looks gross with parser.add_argument... how to make cleaner?
    TODO: add error handling 

    Inserts a new eot record with lots of telemetry data into db

    Returns:
        Cursor object if db operation runs correctly, otherwise, None 
    """
    try:
        recovery_request = True # what is this exactly 
        sql = """
            INSERT INTO EOTRecords (date_rec, symbol_id, station_recorded, unit_addr, brake_pressure, motion, marker_light, turbine, battery_cond, battery_charge, arm_status, signal_strength) VALUES
            (%(date)s, %(symbol_id)s, %(station)s,  %(unit_addr)s, %(brake_pressure)s, %(motion)s, %(marker_light)s, %(turbine)s, %(battery_cond)s, %(battery_charge)s, %(arm_status)s, %(signal_strength)s)
        """
        sql_args = {
            "date": args["date_rec"],
            "station": args["station_id"],
            "unit_addr": args["unit_addr"],
            "brake_pressure": args["brake_pressure"],
            "motion": args["motion"],
            "marker_light": args["marker_light"],
            "turbine": args["turbine"],
            "battery_cond": args["battery_cond"],
            "battery_charge": args["battery_charge"],
            "arm_status": args["arm_status"],
            "signal_strength": args["signal_strength"],
            "symbol_id": args["symbol_id"]
        }

        if args["date_rec"] is None:
                sql_args["date"] = datetime_string
                recovery_request = False

        response = run_exec_cmd(sql, sql_args)

        if response:
            return response, recovery_request
    
        return None
    
    except Exception as e:
        print(f"Error creating EOT record: {e}")
        return None, recovery_request

def get_newest_eot_id(unit_addr: str) -> int:
    """Retrieves latest train id from an eot record 
    
    Args:
        unit_addr: unique id of eot device on train used to detect where a train is?

    Returns: 
        id of a train and its eot record

    Raises:
        No raised exceptions - prints out error and returns None 

    TODO: ERROR HANDLING
    """

    try:
        sql = "SELECT id FROM EOTRecords WHERE unit_addr = %(unit_addr)s"
        sql_args = {"unit_addr": unit_addr}
        eot_id_response = run_get_cmd(sql, sql_args)

        if len(eot_id_response) > 0:
            return eot_id_response[len(eot_id_response) - 1][0]
        
        return None
    
    except Exception as e: 
        print(f"An error occured trying to retrieve 'symbol_id' field for EOTRecords table: {e}")
        return None


def check_for_eot_engine(unit_addr: str) -> int | None:
    """Checks for an engine number from the eotrecords table based on recently tracked train and it's unit address
    
    Args:
        unit_addr: physical location of eot device on train

    Returns: 
        The engine number for a recently tracked train with an eot device based on unit address if the db operation ran fine. Otherwise, None

    Raises: Exception...
    TODO: error handling
    """
    try:
        sql = """
            SELECT engine_num FROM EOTRecords WHERE
            unit_addr = %(unit_addr)s and most_recent = True
        """
        sql_args = {"unit_addr": unit_addr}
        response = run_get_cmd(sql, sql_args)

        if len(response) > 0:
            return response[0][0]
        
        return None
        
    except Exception as e: 
        print(f"An error occured trying to retrieve 'symbol_id' field for EOTRecords table: {e}")
        return None

def check_for_eot_symbol(unit_addr: str) -> int | None:
    """Checks for a symbol from the eotrecords table based on recently tracked train and it's unit address
    
    Args:
        unit_addr: physical location of eot device on train

    Returns: 
        The id of a symbol if the db operation ran fine, else...
    TODO: error handling
    """
    try:
        sql = """
            SELECT symbol_id FROM EOTRecords WHERE 
            unit_addr = %(unit_addr)s and most_recent = True
        """
        sql_args = {"unit_addr": unit_addr}

        response = run_get_cmd(sql, sql_args)

        if len(response) > 0:
            return response[0][0]
        
        return None

    except Exception as e: 
        print(f"An error occured trying to retrieve 'symbol_id' field for EOTRecords table: {e}")
        return None


def attempt_auto_fill_eot_info(unit_addr: str, symb: int) -> bool:
    """Updates latest eot record making sure it's respective train indicates that its the most recently tracked eot device on a train
    
    Args:
        unit_addr: unique id of eot device on train used to detect where a train is?

    Returns:
        True if db operation is successful, otherwise, False if db operation failed

    TODO: error handling
    """ 
    try:
        sql = """
            UPDATE EOTRecords
            SET symbol_id = %(symb_id)s
            WHERE id = %(id)s
        """
        sql_args = {"symb_id": symb, "id": id}
        response = run_exec_cmd(sql, sql_args)

        if response:
            return True
        
        return False
    
    except Exception as e: 
        print(f"An error occured trying to update 'symbol_id' field for EOTRecords table: {e}")
        return False


def add_new_eot_pin(unit_addr: int, eot_id: int) -> bool:
    """Inserts new eot record indiciating a new eot device was tracked recently 

    Args:
        unit_address: location of train with eot device? 
        eot_id: id of an eot record  
    
    Returns:
        True if successful, otherwise, False if the db operation failed.
    
    TODO: error handling
    """
    try: 
        sql = """
        UPDATE EOTRecords
        SET most_recent = false
        WHERE id != %(id)s and unit_addr = %(unit_addr)s and most_recent = true
        """
        sql_args = {"id": eot_id, "unit_addr": unit_addr}
        response = run_exec_cmd(sql, sql_args)
        
        if response:
            return True
        
        return False
    except Exception as e:
        print(f"An error occured trying to update the 'most_recent' field for EOTRecords table for unit_address ({unit_addr}): {e}")
        return False