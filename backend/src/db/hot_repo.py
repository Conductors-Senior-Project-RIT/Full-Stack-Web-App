"""
HOT database layer 

This module handles all database CRUD operations for HOT records
"""
from math import ceil
from typing import Any, Optional, Type
from sqlalchemy import func, select, text
from sqlalchemy.orm.session import Session

from .db_core.models import HOTRecord

from .db_core.exceptions import (
    RepositoryInternalError, RepositoryInvalidArgumentError, repository_error_handler, repository_error_translator
)

from .base_record_repo import RecordRepository


class HOTRepository(RecordRepository[HOTRecord]):
    def __init__(self, session: Session):
        super().__init__(HOTRecord, session, "HOT Record", "hot")
        
       
    # below is train_history.py related
    @repository_error_handler()
    def get_train_history(self, record_id: int, page: int, num_results: int) -> list[dict[str,Any]]:
        from .db_core.models import Station, Symbol
        
        # sql = """
        #         SELECT HOTRecords.id, date_rec, stat.station_name, symbol_id, unit_addr, command, checkbits, parity, verified FROM HOTRecords
        #         INNER JOIN Stations as stat on station_recorded = stat.id
        #         WHERE HOTRecords.id = :id
        #         LIMIT :results_num OFFSET :offset * :results_num
        #         """
        # sql_args = {"id": id, "results_num": num_results, "offset": page - 1}
        stmt = (
            select(
                self.model.id, 
                func.to_char(self.model.date_rec, "YYYY-MM-DD HH24:MI:SS").label("date_rec"),
                Station.station_name,
                self.model.symbol_id,
                self.model.unit_addr,
                self.model.command, 
                self.model.checkbits, 
                self.model.parity, 
                self.model.verified
            )
            .join(Station, Station.id == self.model.station_recorded, isouter=True)
            .where(self.model.id == record_id)
        )
        results = self.session.execute(stmt).all()
        result_dict = self.objs_to_dicts(results)
        return result_dict

    @repository_error_handler()
    def create_train_record(self, args: dict[str, Any], datetime_string: str | None = None) -> int: # type: ignore
        """
        TODO: Namespace is the type for args for post methods in train_history... look more into this
        TODO: run_exec_cmd returns none always... think of what to return lol
        """
        recovery_request = True # what is this lol
        
        sql = """
            INSERT INTO HOTRecords (date_rec, station_recorded, frame_sync, unit_addr, command, checkbits, parity) VALUES
            (:date, :station, :frame_sync, :unit_addr, :command, :checkbits, :parity)
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
            if datetime_string is None:
                raise RepositoryInvalidArgumentError(
                    caller_name=self.__class__.__name__,
                    message="Record timestamp must be provided!",
                    show_error=True
                )
                
            sql_args["date"] = datetime_string
            recovery_request = False
            
            
        result_id = self.session.execute(text(sql), sql_args).scalar_one_or_none()

        if result_id is None:
            raise RepositoryInternalError(
                caller_name=self.__class__.__name__,
                message="Could not create new train record, 0 rows created!",
                show_error=True
            )
            
        return result_id, recovery_request


    # below is for station_handler.py
    @repository_error_handler()
    def get_recent_station_records(self, station_id: int) -> list[dict[str, Any]]:
        """Retrieves the most recent HOT records for a given station id.

        """
        # sql = """
        #     SELECT * FROM HOTRecords 
        #     WHERE station_recorded = :station_id and most_recent = true
        # """
        # args = {"station_id": station_id}
        
        stmt = (
            select(HOTRecord)
            .where(HOTRecord.station_recorded == station_id)
            .where(HOTRecord.most_recent == True)
        )
        results = self.session.execute(stmt).all()
        
        return self.objs_to_dicts(results)


    # below is for record collation
    def get_record_collation(self, page: int, num_results: int, verified: bool | None = None) -> dict[str, list | str]:
        try:
            sql = f"""
                WITH StationChanges AS (
                    SELECT
                        h.id,
                        h.date_rec,
                        h.station_recorded,
                        h.symbol_id,
                        h.unit_addr,
                        h.signal_strength,
                        h.command,
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
                        command,
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
                        g.command,
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
                    TO_CHAR(d.date_rec, 'YYYY-MM-DD HH24:MI:SS') AS date_rec,
                    d.station_name,
                    d.symbol_id,
                    d.unit_addr,
                    d.signal_strength,
                    d.command,
                    d.verified,
                    TO_CHAR(d.first_seen, 'YYYY-MM-DD HH24:MI:SS') AS first_seen,
                    TO_CHAR(d.last_seen, 'YYYY-MM-DD HH24:MI:SS') AS last_seen,
                    d.occurrence_count,
                    AGE(d.last_seen, d.first_seen) AS duration,
                    CASE WHEN d.symbol_id IS NULL THEN NULL ELSE f.symb_name END,
                    d.locomotive_num
                FROM UnitAddrDetails d
                LEFT JOIN Symbols f
                ON d.symbol_id = f.id
                WHERE d.row_num = 1
            """
            
            if verified is not None:
                sql += f"AND verified = {verified}"
            sql += """
                ORDER BY d.date_rec DESC
                LIMIT :results_num OFFSET :offset
            """
            
            args = {"results_num": num_results, "offset": (page - 1) * num_results}
            results = self.session.execute(text(sql), args).all()
            resp = self.objs_to_dicts(results, {"duration", "occurrence_count"})
            
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not collate HOT records: {e}"
            )

        try:
            if verified is None:
                count_sql = """
                    WITH StationChanges AS (
                        SELECT
                            h.id,
                            h.date_rec,
                            h.station_recorded,
                            h.symbol_id,
                            h.unit_addr,
                            h.signal_strength,
                            h.command,
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
                            command,
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
                            g.command,
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
            
            else:   
                count_sql = f"""
                    SELECT COUNT(*) FROM HOTRecords
                    WHERE verified = {verified}
                """
            count = self.session.execute(text(count_sql)).scalar_one()
            
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not count HOT records: {e}"
            )
        

        try:
            results = {
                    "results": resp,
                    "totalPages": ceil(count / num_results),
                }
            return results
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not parse HOT collation results: {e}"
            )
            
        
    # def get_records_by_verification(self, page: int, verified: bool, num_results) -> list[dict[str, Any]]:
    #     verified_str = str(verified).lower()
        
    #     try:
    #         sql = f"""
    #             WITH StationChanges AS (
    #                 SELECT
    #                     e.id,
    #                     e.date_rec,
    #                     e.station_recorded,
    #                     e.symbol_id,
    #                     e.unit_addr,
    #                     e.signal_strength,
    #                     e.verified,
    #                     LAG(e.station_recorded) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) AS prev_station,
    #                     LAG(e.date_rec) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) AS prev_date_rec,
    #                     CASE
    #                         WHEN LAG(e.station_recorded) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) IS DISTINCT FROM e.station_recorded THEN 1
    #                         WHEN e.date_rec - LAG(e.date_rec) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) > INTERVAL '2 hours' THEN 1
    #                         ELSE 0
    #                     END AS is_new_group
    #                 FROM HOTRecords e
    #             ),
    #             GroupedRecords AS (
    #                 SELECT
    #                     id,
    #                     date_rec,
    #                     station_recorded,
    #                     symbol_id,
    #                     unit_addr,
    #                     signal_strength,
    #                     verified,
    #                     SUM(is_new_group) OVER (PARTITION BY unit_addr ORDER BY date_rec) AS group_id
    #                 FROM StationChanges
    #             ),
    #             UnitAddrOccurrences AS (
    #                 SELECT
    #                     unit_addr,
    #                     station_recorded,
    #                     group_id,
    #                     MIN(date_rec) AS first_seen,
    #                     MAX(date_rec) AS last_seen
    #                 FROM GroupedRecords
    #                 GROUP BY unit_addr, station_recorded, group_id
    #             ),
    #             UnitAddrDetails AS (
    #                 SELECT
    #                     g.id,
    #                     g.date_rec,
    #                     stat.station_name,
    #                     g.symbol_id,
    #                     g.unit_addr,
    #                     g.signal_strength,
    #                     g.verified,
    #                     g.station_recorded,
    #                     uo.first_seen,
    #                     uo.last_seen,
    #                     ROW_NUMBER() OVER (PARTITION BY g.unit_addr, g.station_recorded, g.group_id ORDER BY g.date_rec DESC) AS row_num,
    #                     COUNT(*) OVER (PARTITION BY g.unit_addr, g.station_recorded, g.group_id) AS occurrence_count
    #                 FROM GroupedRecords g
    #                 INNER JOIN Stations stat ON g.station_recorded = stat.id
    #                 INNER JOIN UnitAddrOccurrences uo
    #                     ON g.unit_addr = uo.unit_addr
    #                     AND g.station_recorded = uo.station_recorded
    #                     AND g.group_id = uo.group_id
    #             )
    #             SELECT
    #                 d.id,
    #                 TO_CHAR(d.date_rec, 'YYYY-MM-DD HH24:MI:SS') AS date_rec,
    #                 d.station_name,
    #                 d.symbol_id,
    #                 d.unit_addr,
    #                 d.signal_strength,
    #                 d.verified,
    #                 TO_CHAR(d.first_seen, 'YYYY-MM-DD HH24:MI:SS') AS first_seen,
    #                 TO_CHAR(d.last_seen, 'YYYY-MM-DD HH24:MI:SS') AS last_seen,
    #                 d.occurrence_count,
    #                 TO_CHAR(AGE(d.last_seen, d.first_seen), 'YYYY-MM-DD HH24:MI:SS') AS duration
    #             FROM UnitAddrDetails d
    #             WHERE d.row_num = 1
    #             AND d.verified = {verified_str}
    #             ORDER BY d.unit_addr, d.date_rec DESC
    #             LIMIT :results_num OFFSET :offset
    #         """
    #         args = {"results_num": num_results, "offset": (page - 1) * num_results}
    #         results = self.session.execute(text(sql), args).all()
    #         resp = self.objs_to_dicts(results)
    #     except Exception as e:
    #         raise repository_error_translator(
    #             e, self.__class__.__name__, None,
    #             f"Could not retrieve {'verified' if verified else 'unverified'} HOT records: {e}"
    #         )

    #     try:
    #         count_sql = f"""
    #             SELECT COUNT(*) FROM HOTRecords
    #             WHERE verified = {verified_str}
    #         """
    #         count = self.session.execute(text(count_sql)).scalar_one()
    #     except Exception as e:
    #         raise repository_error_translator(
    #             e, self.__class__.__name__, None,
    #             f"Could not count {'verified' if verified else 'unverified'} HOT records: {e}"
    #         )

    #     try:
    #         return {
    #             "results": resp,
    #             "totalPages": ceil(count / num_results)
    #         }
    #     except Exception as e:
    #         raise repository_error_translator(
    #             e, self.__class__.__name__, None,
    #             f"Could not parse HOT verification results: {e}"
    #         )
