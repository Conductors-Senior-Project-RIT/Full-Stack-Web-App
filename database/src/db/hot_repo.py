"""
HOT database layer 

This module handles all database CRUD operations for HOT records
"""

from math import ceil
from typing import Any, NoReturn

from psycopg import Error, sql
from database.src.db.base_record_repo import RecordRepository
from trackSense_db_commands import run_get_cmd, run_exec_cmd

RESULTS_NUM = 250

class HOTRepositoryError(Exception):
    def __init__(self, error_desc: str):
        super().__init__(f"An error occurred in HOTRecords while {error_desc}!")

class HOTRepository(RecordRepository):
    def __init__(self):
        super().__init__("HOTRecords")
        
    # below is train_history.py related
    def get_train_hot_data(self, id: int, page: int, num_results: int) -> list[dict[str,Any]]:
        sql = """
                SELECT HOTRecords.id, date_rec, stat.station_name, sym.symb_name, unit_addr, command, checkbits, parity, verified FROM HOTRecords
                INNER JOIN Stations as stat on station_recorded = stat.id
                INNER JOIN Symbols as sym on symbol_id = sym.id
                WHERE HOTRecords.id = %(id)s
                LIMIT %(results_num)s OFFSET %(offset)s * %(results_num)s
                """
        sql_args = {"id": id, "results_num": num_results, "offset": page - 1}

        try:
            resp = run_get_cmd(sql, sql_args)
            return [
                        {
                            "id": tup[0],
                            "date_rec": tup[1],
                            "station_name": tup[2],
                            "symbol_name": tup[3],
                            "unit_addr": tup[4],
                            "command": tup[5],
                            "checkbits": tup[6],
                            "parity": tup[7],
                            "verified": tup[8],
                        }
                        for tup in resp
            ]
        except Error as e:
            raise HOTRepositoryError(f"retrieving HOT train history: {e}")
        except (IndexError, ValueError) as e:
            raise HOTRepositoryError(f"parsing results: {e}")
            


    def create_hot_record(self, args: dict[str, Any], datetime_string: str) -> None:
        """
        TODO: Namespace is the type for args for post methods in train_history... look more into this
        TODO: run_exec_cmd returns none always... think of what to return lol
        """
        recovery_request = True # what is this lol

        try:
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
        except (IndexError, ValueError) as e:
            raise HOTRepositoryError(f"parsing arguments: {e}")

        sql = """
                INSERT INTO HOTRecords (date_rec, station_recorded, frame_sync, unit_addr, command, checkbits, parity) VALUES
                (%(date)s, %(station)s, %(frame_sync)s, %(unit_addr)s, %(command)s, %(checkbits)s, %(parity)s)
            """
        try:
            return run_exec_cmd(sql, sql_args), recovery_request
        except Error as e:
            raise HOTRepositoryError(f"creating new HOT record: {e}")

    def add_new_hot_pin(self, unit_addr: int, hot_id: int) -> bool:
        update_args = {"id": hot_id, "unit_addr": unit_addr}
        sql_update = """
                    UPDATE HOTRecords
                    SET most_recent = false
                    WHERE id != %(id)s and unit_addr = %(unit_addr)s and most_recent = true
                    """
        run_exec_cmd(sql_update, update_args)

    def get_newest_hot_id(self, unit_addr: str) -> int | None:
        sql_hot_id = """
            SELECT id FROM HOTRecords
            WHERE unit_addr = %(unit_addr)s
        """
        sql_hot_id_args = {"unit_addr": unit_addr}
        resp_hot_id = run_get_cmd(sql_hot_id, sql_hot_id_args)
        return resp_hot_id[len(resp_hot_id) - 1][0]

    def check_for_hot_field(self, unit_addr: str, field_type: str):
        if field_type != "symbol_id" or field_type != "engine_num":
            print("Incorrect database field!")
            return None
        
        sql = """
        SELECT %(field_type)s FROM HOTRecords 
        WHERE unit_addr = %(unit_addr)s and most_recent = True
        """
        params = {"field_type": field_type, "unit_addr": unit_addr}

        resp = run_get_cmd(sql, params)
        if len(resp) == 1:
            return resp[0][0]
        
        return None

    def attempt_auto_fill_hot_info_no_symbol(self, symbol_id: int, hot_id: int) -> bool:
        # id = self.get_newest_eot_id(unit_addr)
        sql_update = """
        UPDATE HOTRecords
        SET symbol_id = %(symb_id)s
        WHERE id = %(id)s
        """
        update_param = {"symb_id": symbol_id, "id": hot_id}

        resp = run_exec_cmd(sql_update, update_param)

    def attempt_auto_fill_hot_info_no_engine(self, engine_id: int, hot_id: int) -> bool:
        sql_update = """
        UPDATE HOTRecords
        SET engine_num = %(engi_id)s
        WHERE id = %(id)s
        """
        update_param = {"engi_id": engine_id, "id": hot_id}

        resp = run_exec_cmd(sql_update, update_param)

    def check_recent_hot_trains(self, unit_addr: str, station_id: int) -> bool:
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

    def update_hot_field(self, record_id: int, field_val, field_type: str):
        if field_type != "symbol_id" or field_type != "engine_num":
            print("Incorrect database field!")
            return False
        
        try:
            args = {"id": record_id, "field_val": field_val}
            query = sql.SQL(
                "UPDATE HOTRecords SET {field_type} = %(field_val)s WHERE id = %(id)s").format(
                field_type=sql.Identifier(field_type)
                )
            resp = run_exec_cmd(query, args)
            print(resp)
            return True
        except Exception as e:
            print(f"An error occurred while updating an EOT record's engine number: {e}")
            return False

    def update_hot_symbol(self, record_id: int, symbol_id: int) -> NoReturn:
        """Updates an HOT record's symbol using the provided record ID and new symbol.
        
        Args:
            record_id (int): The ID of the record to update.
            symbol_id (int): The updated value of the symbol for the EOT record.
        
        Returns:
            bool: True if the update was successful; otherwise, return false if an error occurred.
        """
        args = {"id": record_id, "symbol_id": symbol_id}
        sql = """
            UPDATE HOTRecords
            SET symbol_id = %(symbol_id)s 
            WHERE id = %(id)s
        """
        resp = run_exec_cmd(sql, args)
        print(resp)
        
    def update_hot_engine_num(self, record_id: int, engine_num: int) -> NoReturn:
        """Updates an HOT record's engine number using the provided record ID and engine number.
        
        Args:
            record_id (int): The ID of the record to update.
            engine_num (int): The updated value of the engine number for the EOT record.
            
        Returns:
            bool: True if the update was successful; otherwise, return false if an error occurred.
        """
        args = {"id": record_id, "engine_id": engine_num}
        sql = """
            UPDATE HOTRecords
            SET engine_num = %(engine_id)s 
            WHERE id = %(id)s
        """
        resp = run_exec_cmd(sql, args)
        print(resp)

    # below is for station_handler.py

    def get_most_recent_hot_records(self, station_id: int) -> list[tuple[Any,...]]:
        """Retrieves the most recent HOT records for a given station id.

        """
        hot_records = run_get_cmd(
            "SELECT * FROM HOTRecords WHERE station_recorded = %s and most_recent = true",
            (station_id,),
        )
        return hot_records

    # below is for record collation
    def get_hot_record_collation(self, page: int) -> dict[str, Any]:
        try:
            sql = """
                WITH StationChanges AS (
                    SELECT
                        h.id,
                        h.date_rec,
                        h.station_recorded,
                        h.symbol_id,
                        h.unit_addr,
                        h.signal_strength,
                        h.verified,
                        h.locomotive_num,
                        LAG(h.station_recorded) OVER (PARTITION BY h.unit_addr ORDER BY h.date_rec) AS prev_station,
                        LAG(h.date_rec) OVER (PARTITION BY h.unit_addr ORDER BY h.date_rec) AS prev_date_rec,
                        CASE
                            WHEN LAG(h.station_recorded) OVER (PARTITION BY h.unit_addr ORDER BY h.date_rec) IS DISTINCT FROM h.station_recorded THEN 1
                            WHEN h.date_rec - LAG(h.date_rec) OVER (PARTITION BY h.unit_addr ORDER BY h.date_rec) > INTERVAL '2 hours' THEN 1
                            ELSE 0
                        END AS is_new_group
                    FROM HOTRecords h
                ),
                GroupedRecords AS (
                    SELECT
                        id,
                        date_rec,
                        station_recorded,
                        symbol_id,
                        unit_addr,
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
                        g.signal_strength,
                        g.verified,
                        g.locomotive_num,
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
                SELECT
                    d.id,
                    d.date_rec,
                    d.station_name,
                    d.symbol_id,
                    d.unit_addr,
                    d.signal_strength,
                    d.verified,
                    d.locomotive_num,
                    d.first_seen,
                    d.last_seen,
                    d.occurrence_count,
                    AGE(d.last_seen, d.first_seen) AS duration,
                    f.symb_name
                FROM UnitAddrDetails d
                LEFT JOIN Symbols f
                ON d.symbol_id = f.id
                WHERE d.row_num = 1
                ORDER BY d.date_rec DESC
                LIMIT %(results_num)s OFFSET %(offset)s * %(results_num)s
            """
            args = {"results_num": RESULTS_NUM, "offset": page - 1}
            resp = run_get_cmd(sql, args)
            print(resp)
        except Error as e:
            print(f"DB error occured while attempting to collate HOT records: {e}")
            return None
        except Exception as e:
            print(f"An exception occured while attempting to collate HOT records: {e}")
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
            print(f"DB error occured when attempting to retrieve HOT record counts: {e}")
            return None
        except Exception as e:
            print(f"An exception occured when attempting to retrieve HOT record counts: {e}")
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
                            "signal_strength": tup[5],
                            "verified": tup[6],
                            "locomotive_num": tup[7],
                            "first_seen": tup[8],
                            "last_seen": tup[9],
                            "occurrence_count": str(tup[10]),
                            "duration": str(tup[11]),
                            "symbol_name": tup[12],
                        }
                        for tup in resp
                    ],
                    "totalPages": ceil(count[0][0] / RESULTS_NUM),
                }
            return results
        except Exception as e:
            print(f"An exception ocurred when attempting to parse HOT collation results: {e}")
            return None