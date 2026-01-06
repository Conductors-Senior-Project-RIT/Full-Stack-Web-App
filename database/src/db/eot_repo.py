"""
EOT database layer 

This module handles all database CRUD operations for EOT records
"""

from math import ceil
from typing import Any
from base_record_repo import RecordRepository
from database_status import *
from trackSense_db_commands import run_get_cmd, run_exec_cmd
from psycopg import Error, OperationalError

RESULTS_NUM = 250

class EOTRepository(RecordRepository):
    def __init__(self):
        super().__init__("EOTRecords", "EOT Record", "eot")

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
        
    def get_train_history(self, id: int, page: int, num_results: int) -> list[dict[str,Any]]:
        """ Retrieves EOT records for a specific train id
        
        Args:
            id: The id of an EOT train record to retrieve.
            page: The page of records to return.

        Returns:
            If db operation is successful, a list of tuples containing EOT records for a specific train id is returned, otherwise, None
        
        Raises:
            No raised exceptions - prints out error and returns None  
    
        What it will replace: 
            def get_eot(self, id: int, page: int) -> Response in train_history.py

        TODO: improve error handling/ documentation 
        TODO: integrate this function to replace sql queries in train_history.py's def get_eot() 
        TODO: Format returned collection
        TODO: what is symbol_id for a train, is it it's unique identifier?
        """
        
        # TODO: Move  to db
        sql = """SELECT EOTRecords.id, date_rec, stat.station_name, sym.symb_name, unit_addr, brake_pressure, motion, marker_light, turbine, battery_cond, battery_charge, arm_status, signal_strength, verified FROM EOTRecords
                INNER JOIN Stations as stat on station_recorded = stat.id
                INNER JOIN Symbols as sym on symbol_id = sym.id"""
        
        sql += "WHERE EOTRecords.id = %(id)s ORDER BY EOTRecords.id Desc" if id == 1 else "ORDER BY date_rec DESC"
        sql += "LIMIT %(results_num)s OFFSET %(offset)s * %(results_num)s"
        
        sql_args = {"results_num": num_results, "offset": page - 1}
        sql_args["id"] = id
        
        try:
            resp = run_get_cmd(sql, sql_args)
            results = [
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
                    ]
            
            if id == 1:    
                return results
        
            count_sql = """SELECT COUNT(*) FROM EOTRecords"""
            count = run_get_cmd(count_sql)

            return {
                    "results": results,
                    "totalPages": ceil(count[0][0] / num_results),
                }
        
        except OperationalError as e:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Could not retrieve EOT train history: {e}")
        except (IndexError, ValueError, TypeError) as e:
            raise RepositoryParsingError(f"Could not parse results: {e}")

    def create_train_record(self, args: dict[str, Any], datetime_string: str) -> tuple[int, bool]:  #post_eot()
        """Inserts a new eot record in EOTRecords table

        Args:
            datetime_string: date and time when an eot record is created
            args: named arguments to pass into parameterized query

        Returns:
            , otherwise, None

        Raises:
            RepositoryError if error arises in database query or argument parsing.  

        TODO: integrate this function to replace sql queries in train_history.py's post_eot() | train_history post() looks gross with parser.add_argument... how to make cleaner?
        TODO: improve error handling/ documentation | CHANGE RETURN TYPE 
        """
        recovery_request = True # what is this exactly 
            
        try:
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

            results = run_exec_cmd(sql, sql_args)
            if results < 1:
                raise RepositoryInternalError("Could not create new train record, 0 rows created!")
            return results, recovery_request
        
        except OperationalError as e:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Could not create new EOT record: {e}")
        except (IndexError, ValueError) as e:
            raise RepositoryParsingError(f"Could not parse arguments: {e}")


    # below is for station_handler.py 
    def get_recent_station_records(self, station_id: int) -> list[tuple[Any,...]]:
        """Retrieves most recent eot records for a given station id.

        """
        eot_records = run_get_cmd(
            "SELECT * FROM EOTRecords WHERE station_recorded = %s and most_recent = true INNER JOIN Symbols ON EOTRecords.symbol_id = Symbols.id INNER JOIN Engine_Numbers ON EOTRecords.engine_num = Engine_Numbers.id",
            (station_id,)
        )
        return eot_records
    
    
    def parse_station_records(self, station_records: list[tuple[Any, ...]]) -> list[dict[str, Any]]:
        try:
            if station_records is None:
                return []
            eot_records = [
                {
                    "date_rec": record[1],
                    "unit_addr": record[4],
                    "brake_pressure": record[5],
                    "motion": record[6],
                    "marker_light": record[7],
                    "turbine": record[8],
                    "battery_cond": record[9],
                    "battery_charge": record[10],
                    "arm_status": record[11],
                    "signal_stength": record[12],
                }
                for record in station_records
            ]
            return eot_records
        
        except IndexError as e:
            raise RepositoryParsingError(f"Could not parse EOT station records: {e}")


    # below is for eot_collation
    def get_record_collation(self, page: int) -> list[dict[str, Any]]:
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
        except OperationalError:
            raise RepositoryTimeoutError("Could not collate EOT records!")
        except Error as e:
            raise RepositoryInternalError(f"Could not collate EOT records: {e}")
        
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
        except OperationalError:
            raise RepositoryTimeoutError("Could not count EOT records!")
        except Error as e:
            raise RepositoryInternalError(f"Could not count EOT records: {e}")
        
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
                    "totalPages": ceil(count[0][0] / RESULTS_NUM)
                }
            return results
        except (IndexError, ValueError, TypeError, ZeroDivisionError) as e:
            raise RepositoryParsingError(f"Could not parse EOT collation results: {e}")
    
    # Record/admin verification
    def get_records_by_verification(self, page: int, verified: bool):
        verified_str = str(verified).lower()
        
        try:
            sql = f"""
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
                    AGE(d.last_seen, d.first_seen) AS duration
                FROM UnitAddrDetails d
                WHERE d.row_num = 1
                AND d.verified = {verified_str}
                ORDER BY d.date_rec DESC -- Order by the most recent date
                LIMIT %(results_num)s OFFSET %(offset)s * %(results_num)s
            """
            args = {"results_num": RESULTS_NUM, "offset": page - 1}
            resp = run_get_cmd(sql, args)
        except OperationalError:
            raise RepositoryTimeoutError(f"Could not retrieve {'verified' if verified else 'unverified'} EOT records!")
        except Error as e:
            raise RepositoryInternalError(f"Could not retrieve {'verified' if verified else 'unverified'} EOT records: {str(e)}")
        
        try:
            count_sql = f"""
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
                SELECT COUNT(*) 
                FROM UnitAddrDetails 
                WHERE row_num = 1 AND verified = {verified_str};
            """
            count = run_get_cmd(count_sql)
        except OperationalError:
            raise RepositoryTimeoutError(f"Could not count {'verified' if verified else 'unverified'} EOT records!")
        except Error as e:
            raise RepositoryInternalError(f"Could not count {'verified' if verified else 'unverified'} EOT records: {str(e)}")
            
        try:
            return {
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
                        "occurrence_count": str(tup[16]),
                        "duration": str(tup[17]),
                    }
                    for tup in resp
                ],
                "totalPages": ceil(count[0][0] / RESULTS_NUM)
            }
        except (IndexError, ValueError, TypeError, ZeroDivisionError) as e:
            raise RepositoryParsingError(f"Could not parse EOT verification results: {e}")