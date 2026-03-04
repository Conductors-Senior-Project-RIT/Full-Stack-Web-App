"""
HOT database layer 

This module handles all database CRUD operations for HOT records
"""
from math import ceil
from typing import Any
from sqlalchemy import text

from .database_core import RepositoryInternalError, repository_error_translator
from .base_record_repo import RecordRepository

RESULTS_NUM = 250


class HOTRepository(RecordRepository):
    def __init__(self, session):
        super().__init__(
            session,
            "HOTRecords", 
            "HOT Record", 
            "hot"
        )
        
    # below is train_history.py related
    def get_train_history(self, id: int, page: int, num_results: int) -> list[dict[str,Any]]:
        sql = """
                SELECT HOTRecords.id, date_rec, stat.station_name, sym.symb_name, unit_addr, command, checkbits, parity, verified FROM HOTRecords
                INNER JOIN Stations as stat on station_recorded = stat.id
                INNER JOIN Symbols as sym on symbol_id = sym.id
                WHERE HOTRecords.id = :id
                LIMIT :results_num OFFSET :offset * :results_num
                """
        sql_args = {"id": id, "results_num": num_results, "offset": page - 1}
        
        resp = [row._asdict() for row in self.session.execute(text(sql), sql_args).all()]
        return [
                    {
                        "id": row[0],
                        "date_rec": row[1],
                        "station_name": row[2],
                        "symbol_name": row[3],
                        "unit_addr": row[4],
                        "command": row[5],
                        "checkbits": row[6],
                        "parity": row[7],
                        "verified": row[8],
                    }
                    for row in resp
        ]


    def create_train_record(self, args: dict[str, Any], datetime_string: str) -> tuple[int, bool]:
        """
        TODO: Namespace is the type for args for post methods in train_history... look more into this
        TODO: run_exec_cmd returns none always... think of what to return lol
        """
        recovery_request = True # what is this lol
        
        sql = """
            INSERT INTO HOTRecords (date_rec, station_recorded, frame_sync, unit_addr, command, checkbits, parity) VALUES
            (%(date)s, %(station)s, %(frame_sync)s, %(unit_addr)s, %(command)s, %(checkbits)s, %(parity)s)
            RETURNING id
        """
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

        result = self.session.execute(text(sql), sql_args).scalar_one_or_none()
        if not result:
            raise RepositoryInternalError(
                caller_name=self.__class__.__name__,
                message="Could not create new train record, 0 rows created!",
                show_error=True
            )
        
        return result, recovery_request


    # below is for station_handler.py
    def get_recent_station_records(self, station_id: int) -> list[tuple[Any,...]]:
        """Retrieves the most recent HOT records for a given station id.

        """
        sql = """
            SELECT * FROM HOTRecords 
            WHERE station_recorded = :station_id and most_recent = true
        """
        args = {"station_id": station_id}
        
        return self.session.execute(text(sql), args).all()
    
        
    def parse_station_records(self, station_records: list[tuple[Any, ...]]) -> list[dict[str, Any]] | None:
        if station_records is None:
            return []
        hot_records = [
            {
                "id": record[0],
                "date_rec": record[1],
                "frame_sync": record[3],
                "unit_addr": record[4],
                "command": record[5],
                "checkbits": record[6],
                "parity": record[7],
            }
            for record in station_records
        ]
        return hot_records


    # below is for record collation
    def get_record_collation(self, page: int) -> list[dict[str, Any]]:
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
                LIMIT :results_num OFFSET :offset * :results_num
            """
            args = {"results_num": RESULTS_NUM, "offset": page - 1}
            resp = [row._asdict() for row in self.session.execute(text(sql), args)]
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not collate HOT records: {e}"
            )

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
            count = self.session.execute(text(count_sql)).scalar_one()
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not count HOT records: {e}"
            )
            
        try:
            results = {
                    "results": [
                        {
                            "id": row[0],
                            "date_rec": row[1],
                            "station_name": row[2],
                            "symbol_id": row[3],
                            "unit_addr": row[4],
                            "signal_strength": row[5],
                            "verified": row[6],
                            "locomotive_num": row[7],
                            "first_seen": row[8],
                            "last_seen": row[9],
                            "occurrence_count": str(row[10]),
                            "duration": str(row[11]),
                            "symbol_name": row[12],
                        }
                        for row in resp
                    ],
                    "totalPages": ceil(count / RESULTS_NUM),
                }
            return results
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not parse HOT collation results: {e}"
            )
            
        
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
                        e.signal_strength,
                        e.verified,
                        LAG(e.station_recorded) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) AS prev_station,
                        LAG(e.date_rec) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) AS prev_date_rec,
                        CASE
                            WHEN LAG(e.station_recorded) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) IS DISTINCT FROM e.station_recorded THEN 1
                            WHEN e.date_rec - LAG(e.date_rec) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) > INTERVAL '2 hours' THEN 1
                            ELSE 0
                        END AS is_new_group
                    FROM HOTRecords e
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
                    d.first_seen,
                    d.last_seen,
                    d.occurrence_count,
                    AGE(d.last_seen, d.first_seen) AS duration
                FROM UnitAddrDetails d
                WHERE d.row_num = 1
                AND d.verified = {verified_str}
                ORDER BY d.unit_addr, d.date_rec DESC
                LIMIT :results_num OFFSET :offset * :results_num
            """
            args = {"results_num": RESULTS_NUM, "offset": page - 1}
            resp = [row._asdict() for row in self.session.execute(text(sql), args).all()]
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not retrieve {'verified' if verified else 'unverified'} HOT records: {e}"
            )

        try:
            count_sql = f"""
                SELECT COUNT(*) FROM HOTRecords
                WHERE verified = {verified_str}
            """
            count = self.session.execute(text(count_sql)).scalar_one()
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not count {'verified' if verified else 'unverified'} HOT records: {e}"
            )

        try:
            return {
                "results": [
                    {
                        "id": row[0],
                        "date_rec": row[1],
                        "station_name": row[2],
                        "symbol_id": row[3],
                        "unit_addr": row[4],
                        "signal_strength": row[5],
                        "verified": row[6],
                        "first_seen": row[7],
                        "last_seen": row[8],
                        "occurrence_count": row[9],
                        "duration": str(row[10]),
                    }
                    for row in resp
                ],
                "totalPages": ceil(count[0][0] / RESULTS_NUM)
            }
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not parse HOT verification results: {e}"
            )
