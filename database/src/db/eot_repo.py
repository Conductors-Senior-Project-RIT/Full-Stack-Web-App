"""
EOT database layer 

This module handles all database CRUD operations for EOT records
"""

from math import ceil
from typing import Any, NoReturn
from database.src.db.base_record_repo import RecordRepository
from database.src.db.symbol_db import get_symbol_name
from trackSense_db_commands import run_get_cmd, run_exec_cmd
from psycopg import Error, sql

RESULTS_NUM = 250

class EOTRepository(RecordRepository):
    def __init__(self):
        super().__init__("EOTRecords")

    # below is train_history.py related
    def get_total_count_of_eot_records(self) -> int:
        """Retrieves total amount of records in EOTRecords table

        Returns:
            If db operation is successful, number of records in EOTRecords table, otherwise, None
        
        Raises:
            No raised exceptions - prints out error and returns None  

        TODO: integrate this function to replace sql queries in train_history.py's def get_eot()
        
        TODO: improve error handling/ documentation 
        """

        try:
            response = run_get_cmd("SELECT COUNT(*) FROM EOTRecords")

            if response:
                return response[0][0]
            
            return -1
        except Exception as e:
            print(f"Error getting EOT record count: {e}")
            return -1
        
    def get_eot_data_by_train_id(self, id: int, page: int, num_results: int) -> list[tuple[Any,...]] | None:
        """ Retrieves eot records for a specific train id
        
        Args:
            id: The id of an eot train record to retrieve.
            page: The page of records to return.

        Returns:
            If db operation is successful, a list of tuples containing eot records for a specific train id is returned, otherwise, None
        
        Raises:
            No raised exceptions - prints out error and returns None  
    
        What it will replace: 
            def get_eot(self, id: int, page: int) -> Response in train_history.py

        TODO: improve error handling/ documentation 
        TODO: integrate this function to replace sql queries in train_history.py's def get_eot() 
        TODO: Format returned collection
        TODO: what is symbol_id for a train, is it it's unique identifier?
        """

        if not isinstance(id, int):
            raise ValueError(f"id ({id}) is not an integer")
        
        if not isinstance(page, int):
            raise ValueError(f"page ({page}), is not an integer")
        
        if not isinstance(num_results, int):
            raise ValueError(f"num_results ({num_results}), is not an integer")

        # TODO: Move  to db
        try:
            sql = """SELECT EOTRecords.id, date_rec, stat.station_name, symbol_id, unit_addr, brake_pressure, motion, marker_light, turbine, battery_cond, battery_charge, arm_status, signal_strength, verified FROM EOTRecords
                    INNER JOIN Stations as stat on station_recorded = stat.id"""
            
            sql += "WHERE EOTRecords.id = %(id)s ORDER BY EOTRecords.id Desc" if id == 1 else "ORDER BY date_rec DESC"
            sql += "LIMIT %(results_num)s OFFSET %(offset)s * %(results_num)s"
            
            sql_args = {"results_num": num_results, "offset": page - 1}
            if id == 1:
                sql_args["id"] = id
                resp = run_get_cmd(sql, sql_args) # BUG: move this LOC above if block so it's accessible by else block as well
                # TODO: Fix inconsistent return payload
                return [
                        {
                            "id": tup[0],
                            "date_rec": tup[1],
                            "station_name": tup[2],
                            "symbol_name": get_symbol_name(tup[3]),
                            "unit_addr": tup[4],
                            "brake_pressure": tup[5],
                            "motion": tup[6],
                            "marker_light": tup[7],
                            "turbine": tup[8],
                            "battery_cond": tup[9],
                            "battery_charge": tup[10],
                            "arm_status": tup[11],
                            "signal_strength": tup[12],
                            "verified": tup[13],
                        }
                        for tup in resp
                    ]
                    
            # BUG: in the else block it is trying to reference "resp" but it's out of scope...
            else:
                count_sql = """SELECT COUNT(*) FROM EOTRecords"""
                count = run_get_cmd(count_sql)

                return {
                        "results": [
                            {
                                "id": tup[0],
                                "date_rec": tup[1],
                                "station_name": tup[2],
                                "symbol_name": tup[3],
                                "unit_addr": tup[4],
                                "brake_pressure": tup[5],
                                "motion": tup[6],
                                "marker_light": tup[7],
                                "turbine": tup[8],
                                "battery_cond": tup[9],
                                "battery_charge": tup[10],
                                "arm_status": tup[11],
                                "signal_strength": tup[12],
                                "verified": tup[13],
                            }
                            for tup in resp
                        ],
                        "totalPages": ceil(count[0][0] / num_results),
                    }
        except Error as e:
            print(f"Encountered a database error when attempting to retrieve EOT records: {e}")
        except Exception as e:
            print(f"Encountered an exception when attempting to retrieve EOT records: {e}")
        return None

    def create_eot_record(self, args: dict[str, Any], datetime_string: str) -> tuple | None:  #post_eot()
        """Inserts a new eot record in EOTRecords table

        Args:
            datetime_string: date and time when an eot record is created
            args: named arguments to pass into parameterized query

        Returns:
            , otherwise, None

        Raises:
            No raised exceptions - prints out error and returns None  

        TODO: integrate this function to replace sql queries in train_history.py's post_eot() | train_history post() looks gross with parser.add_argument... how to make cleaner?
        TODO: improve error handling/ documentation | CHANGE RETURN TYPE 
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

            response = run_exec_cmd(sql, sql_args) # these guys were tweaking, this literally returns none no matter what lol

            if response:
                return response, recovery_request
        
            return None
        
        except Exception as e:
            print(f"Error creating EOT record: {e}")
            return None, recovery_request

    def get_newest_eot_id(self, unit_addr: str) -> int | None:
        """Retrieves latest train id from an eot record 
        
        Args:
            unit_addr: location of train with eot device?

        Returns: 
            id of a train and its eot record

        Raises:
            No raised exceptions - prints out error and returns None 

        TODO: improve error handling/ documentation 
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

    def check_for_eot_field(self, unit_addr: str, field_type: str) -> int | None:
        if field_type != "symbol_id" or field_type != "engine_num":
            print("Incorrect database field!")
            return None
        
        sql = """
        SELECT %(field_type)s FROM EOTRecords 
        WHERE unit_addr = %(unit_addr)s and most_recent = True
        """
        params = {"field_type": field_type, "unit_addr": unit_addr}

        resp = run_get_cmd(sql, params)
        if len(resp) == 1:
            return resp[0][0]
        
        return None



    def check_for_eot_engine(self, unit_addr: str) -> int | None:
        """Checks for an engine number from the eotrecords table based on recently tracked train and it's unit address
        
        Args:
            unit_addr: location of train with eot device?

        Returns: 
            The engine number for a recently tracked train with an eot device based on unit address if the db operation ran fine. Otherwise, None

        Raises:
            No raised exceptions - prints out error and returns None  

        TODO: improve error handling/ documentation 
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

    def check_for_eot_symbol(self, unit_addr: str) -> int | None:
        """Checks for a symbol from the eotrecords table based on recently tracked train and it's unit address
        
        Args:
            unit_addr: location of train with eot device?

        Returns: 
            If the db operation is successful, the id of a symbol, otherwise None

        Raises:
            No raised exceptions - prints out error and returns None  
        
        TODO: improve error handling/ documentation 
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

    def update_eot_field(self, record_id: int, field_val, field_type: str):
        if field_type != "symbol_id" or field_type != "engine_num":
            print("Incorrect database field!")
            return False
        
        try:
            args = {"id": record_id, "field_val": field_val}
            query = sql.SQL(
                "UPDATE EOTRecords SET {field_type} = %(field_val)s WHERE id = %(id)s").format(
                field_type=sql.Identifier(field_type)
                )
            resp = run_exec_cmd(query, args)
            print(resp)
            return True
        except Exception as e:
            print(f"An error occurred while updating an HOT record's engine number: {e}")
            return False

    def update_eot_symbol(self, record_id: int, symbol_id: int) -> bool:
        """Updates an EOT record's symbol using the provided record ID and new symbol.
        
        Args:
            record_id (int): The ID of the record to update.
            symbol_id (int): The updated value of the symbol for the EOT record.
        
        Returns:
            bool: True if the update was successful; otherwise, return false if an error occurred.
        """
        args = {"id": record_id, "symbol_id": symbol_id}
        sql = """
            UPDATE EOTRecords
            SET symbol_id = %(symbol_id)s 
            WHERE id = %(id)s
        """
        resp = run_exec_cmd(sql, args)
        print(resp)
        
        
    def update_eot_engine_num(self, record_id: int, engine_num: int) -> bool:
        """Updates an EOT record's engine number using the provided record ID and engine number.
        
        Args:
            record_id (int): The ID of the record to update.
            engine_num (int): The updated value of the engine number for the EOT record.
            
        Returns:
            bool: True if the update was successful; otherwise, return false if an error occurred.
        """
        try:
            args = {"id": record_id, "engine_id": engine_num}
            sql = """
                UPDATE EOTRecords
                SET engine_num = %(engine_id)s 
                WHERE id = %(id)s
            """
            resp = run_exec_cmd(sql, args)
            print(resp)
            return True
        except Exception as e:
            print(f"An error occurred while updating an EOT record's engine number: {e}")
            return False


    def attempt_auto_fill_eot_info_no_symbol(self, symbol_id: int, hot_id: int) -> bool:
        """Updates latest eot record making sure it's respective train indicates that its the most recently tracked eot device on a train
        
        Args:
            unit_addr: location of train with eot device?
            symbol_id

        Returns:
            True if db operation is successful, otherwise, False if db operation failed

        Raises:
            No raised exceptions - prints out error and returns None  
        
        TODO: improve error handling/ documentation 
        """ 
        try:
            sql = """
                UPDATE EOTRecords
                SET symbol_id = %(symb_id)s
                WHERE id = %(id)s
            """
            sql_args = {"symb_id": symbol_id, "id": hot_id}
            response = run_exec_cmd(sql, sql_args)

            if response:
                return True
            
            return False
        
        except Exception as e: 
            print(f"An error occured trying to update 'symbol_id' field for EOTRecords table: {e}")
            return False


    def add_new_eot_pin(self, unit_addr: int, eot_id: int) -> bool:
        """Inserts new eot record indiciating a new eot device was tracked recently 

        Args:
            unit_addr: location of train with eot device?
            eot_id: id of an eot record  
        
        Returns:
            True if successful, otherwise, False if the db operation failed.

        Raises:
            No raised exceptions - prints out error and returns None  

        TODO: improve error handling/ documentation 
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
        
    def check_recent_eot_trains(self, unit_addr: str, station_id: int) -> bool:
        """Checks if there's any records (trains) from EOTRecords that were detected in the last 10 minutes

        Args:
            unit_addr: location of train with eot device? 
            eot_id: id of an eot record  
        
        Returns:
            True if a train with an eot device was recorded within the last 10 minutes, otherwise False

        Raises:
            No raised exceptions - prints out error and returns None  

        TODO: improve error handling/ documentation 
        """
        try: 
            sql = """
            SELECT * FROM EOTRecords
            WHERE unit_addr = %(unit_address)s 
            AND station_recorded = %(station_id)s AND date_rec >= NOW() - INTERVAL '10 minutes'
            """

            sql_args = {"unit_address": unit_addr, "station_id": station_id}

            response = run_exec_cmd(sql, sql_args)
            
            if response:
                return True
            
            return False
        
        except Exception as e:
            print(f"An error occured trying to update the 'most_recent' field for EOTRecords table for unit_address ({unit_addr}): {e}")
            return False

    # below is for station_handler.py 
    # TODO: remove code that was moved into generic_record_db.py 

    def get_most_recent_eot_records(self, station_id: int) -> list[tuple[Any,...]]:
        """Retrieves most recent eot records for a given station id.

        """
        eot_records = run_get_cmd(
            "SELECT * FROM EOTRecords WHERE station_recorded = %s and most_recent = true INNER JOIN Symbols ON EOTRecords.symbol_id = Symbols.id INNER JOIN Engine_Numbers ON EOTRecords.engine_num = Engine_Numbers.id",
            (station_id,)
        )
        return eot_records

    # below is for eot_collation
    def get_eot_record_collation(self, page: int) -> dict[str, Any]:
        try:
            sql = """
                WITH StationChanges AS (
                    SELECT
                        e.id,
                        e.date_rec,
                        e.station_recorded,
                        e.symbol_id,
                        e.unit_addr,
                        e.brake_pressure,
                        e.motion,
                        e.marker_light,
                        e.turbine,
                        e.battery_cond,
                        e.battery_charge,
                        e.arm_status,
                        e.signal_strength,
                        e.verified,
                        e.locomotive_num,
                        LAG(e.station_recorded) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) AS prev_station,
                        LAG(e.date_rec) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) AS prev_date_rec,
                        CASE
                            WHEN LAG(e.station_recorded) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) IS DISTINCT FROM e.station_recorded THEN 1
                            WHEN e.date_rec - LAG(e.date_rec) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) > INTERVAL '2 hours' THEN 1
                            ELSE 0
                        END AS is_new_group
                    FROM EOTRecords e
                ),
                GroupedRecords AS (
                    SELECT
                        id,
                        date_rec,
                        station_recorded,
                        symbol_id,
                        unit_addr,
                        brake_pressure,
                        motion,
                        marker_light,
                        turbine,
                        battery_cond,
                        battery_charge,
                        arm_status,
                        signal_strength,
                        verified,
                        locomotive_num,
                        SUM(is_new_group) OVER (PARTITION BY unit_addr ORDER BY date_rec) AS group_id
                    FROM StationChanges
                ),
                UnitAddrOccurrences AS (
                    SELECT
                        unit_addr,
                        station_recorded,
                        group_id,
                        MIN(date_rec) AS first_seen,
                        MAX(date_rec) AS last_seen
                    FROM GroupedRecords
                    GROUP BY unit_addr, station_recorded, group_id
                ),
                UnitAddrDetails AS (
                    SELECT
                        g.id,
                        g.date_rec,
                        stat.station_name,
                        g.symbol_id,
                        g.unit_addr,
                        g.brake_pressure,
                        g.motion,
                        g.marker_light,
                        g.turbine,
                        g.battery_cond,
                        g.battery_charge,
                        g.arm_status,
                        g.signal_strength,
                        g.verified,
                        g.station_recorded,
                        g.locomotive_num,
                        uo.first_seen,
                        uo.last_seen,
                        ROW_NUMBER() OVER (PARTITION BY g.unit_addr, g.station_recorded, g.group_id ORDER BY g.date_rec DESC) AS row_num,
                        COUNT(*) OVER (PARTITION BY g.unit_addr, g.station_recorded, g.group_id) AS occurrence_count
                    FROM GroupedRecords g
                    INNER JOIN Stations stat ON g.station_recorded = stat.id
                    INNER JOIN UnitAddrOccurrences uo
                        ON g.unit_addr = uo.unit_addr
                        AND g.station_recorded = uo.station_recorded
                        AND g.group_id = uo.group_id
                )
                SELECT
                    d.id,
                    d.date_rec,
                    d.station_name,
                    d.symbol_id,
                    d.unit_addr,
                    d.brake_pressure,
                    d.motion,
                    d.marker_light,
                    d.turbine,
                    d.battery_cond,
                    d.battery_charge,
                    d.arm_status,
                    d.signal_strength,
                    d.verified,
                    d.first_seen,
                    d.last_seen,
                    d.occurrence_count,
                    AGE(d.last_seen, d.first_seen) AS duration,
                    CASE WHEN d.symbol_id IS NULL THEN NULL ELSE f.symb_name END,
                    d.locomotive_num
                FROM UnitAddrDetails d
                LEFT JOIN Symbols f
                ON d.symbol_id = f.id
                WHERE d.row_num = 1
                ORDER BY d.date_rec DESC
                LIMIT %(results_num)s OFFSET %(offset)s * %(results_num)s
            """
            args = {"results_num": RESULTS_NUM, "offset": page - 1}
            resp = run_get_cmd(sql, args)
        except Error as e:
            print(f"DB error occured while attempting to collate EOT records: {e}")
            return None
        except Exception as e:
            print(f"An exception occured while attempting to collate EOT records: {e}")
            return None
        
        try:
            count_sql = """
                WITH StationChanges AS (
                    SELECT
                        e.id,
                        e.date_rec,
                        e.station_recorded,
                        e.symbol_id,
                        e.unit_addr,
                        e.brake_pressure,
                        e.motion,
                        e.marker_light,
                        e.turbine,
                        e.battery_cond,
                        e.battery_charge,
                        e.arm_status,
                        e.signal_strength,
                        e.verified,
                        LAG(e.station_recorded) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) AS prev_station,
                        LAG(e.date_rec) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) AS prev_date_rec,
                        CASE
                            WHEN LAG(e.station_recorded) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) IS DISTINCT FROM e.station_recorded THEN 1
                            WHEN e.date_rec - LAG(e.date_rec) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) > INTERVAL '2 hours' THEN 1
                            ELSE 0
                        END AS is_new_group
                    FROM EOTRecords e
                ),
                GroupedRecords AS (
                    SELECT
                        id,
                        date_rec,
                        station_recorded,
                        symbol_id,
                        unit_addr,
                        brake_pressure,
                        motion,
                        marker_light,
                        turbine,
                        battery_cond,
                        battery_charge,
                        arm_status,
                        signal_strength,
                        verified,
                        SUM(is_new_group) OVER (PARTITION BY unit_addr ORDER BY date_rec) AS group_id
                    FROM StationChanges
                ),
                UnitAddrOccurrences AS (
                    SELECT
                        unit_addr,
                        station_recorded,
                        group_id,
                        MIN(date_rec) AS first_seen,
                        MAX(date_rec) AS last_seen
                    FROM GroupedRecords
                    GROUP BY unit_addr, station_recorded, group_id
                ),
                UnitAddrDetails AS (
                    SELECT
                        g.id,
                        g.date_rec,
                        stat.station_name,
                        g.symbol_id,
                        g.unit_addr,
                        g.brake_pressure,
                        g.motion,
                        g.marker_light,
                        g.turbine,
                        g.battery_cond,
                        g.battery_charge,
                        g.arm_status,
                        g.signal_strength,
                        g.verified,
                        g.station_recorded,
                        uo.first_seen,
                        uo.last_seen,
                        ROW_NUMBER() OVER (PARTITION BY g.unit_addr, g.station_recorded, g.group_id ORDER BY g.date_rec DESC) AS row_num,
                        COUNT(*) OVER (PARTITION BY g.unit_addr, g.station_recorded, g.group_id) AS occurrence_count
                    FROM GroupedRecords g
                    INNER JOIN Stations stat ON g.station_recorded = stat.id
                    INNER JOIN UnitAddrOccurrences uo
                        ON g.unit_addr = uo.unit_addr
                        AND g.station_recorded = uo.station_recorded
                        AND g.group_id = uo.group_id
                )
                SELECT COUNT(*) FROM UnitAddrDetails WHERE row_num = 1;
            """
            count = run_get_cmd(count_sql)
        
        except Error as e:
            print(f"DB error occured when attempting to retrieve EOT record counts: {e}")
            return None
        except Exception as e:
            print(f"An exception occured when attempting to retrieve EOT record counts: {e}")
            return None
        
        try:
            results = {
                    "results": [
                        {
                            "id": tup[0],
                            "date_rec": tup[1],
                            "station_name": tup[2],
                            "symbol_id": tup[3],
                            "unit_addr": tup[4],
                            "brake_pressure": tup[5],
                            "motion": tup[6],
                            "marker_light": tup[7],
                            "turbine": tup[8],
                            "battery_cond": tup[9],
                            "battery_charge": tup[10],
                            "arm_status": tup[11],
                            "signal_strength": tup[12],
                            "verified": tup[13],
                            "first_seen": tup[14],
                            "last_seen": tup[15],
                            "ocurrence_count": str(tup[16]),
                            "duration": str(tup[17]),
                            "symbol_name": tup[18],
                            "locomotive_num": tup[19],
                        }
                        for tup in resp
                    ],
                    "totalPages": ceil(count[0][0] / RESULTS_NUM),
                }
            return results
        except Exception as e:
            print(f"An exception ocurred when attempting to parse EOT collation results: {e}")
            return None
        
