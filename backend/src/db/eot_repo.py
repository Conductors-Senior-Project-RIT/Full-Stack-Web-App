"""
EOT database layer

This module handles all database CRUD operations for EOT records
"""

from math import ceil
from typing import Any
from sqlalchemy import desc, func, select, text

from .db_core.models import EOTRecord
from .base_record_repo import RecordRepository
from .db_core.exceptions import (
    RepositoryInternalError, RepositoryInvalidArgumentError, repository_error_translator, repository_error_handler
)


class EOTRepository(RecordRepository[EOTRecord]): 
    def __init__(self, session):
        super().__init__(EOTRecord, session, "EOT Record", "eot")


    # below is train_history.py related
    def get_train_history(self, id: int, page: int, num_results: int) -> (
        list[dict[str, Any]] | dict[str, list[dict[str, Any]] | int]):
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

        TODO: improve documentation 
        TODO: integrate this function to replace sql queries in train_history.py's def get_eot() 
        TODO: Format returned collection
        TODO: what is symbol_id for a train, is it it's unique identifier?
        """
        from .db_core.models import Station, Symbol
        
        stmt = (
            select(
                self.model.id,
                func.to_char(self.model.date_rec, "YYYY-MM-DD HH24:MI:SS").label("date_rec"),
                Station.station_name,
                self.model.unit_addr,
                self.model.brake_pressure,
                self.model.motion,
                self.model.marker_light,
                self.model.turbine,
                self.model.battery_cond,
                self.model.battery_charge,
                self.model.arm_status,
                self.model.signal_strength,
                self.model.verified
            )
            .join(Station, Station.id == self.model.station_recorded)
        )
        
        if id != -1:
            stmt = stmt.where(self.model.id == id).order_by(desc(self.model.id))
        else:
            stmt = stmt.order_by(desc(self.model.date_rec)).limit(num_results).offset((page - 1) * num_results)
        
        # sql = """SELECT EOTRecords.id, date_rec, stat.station_name, Symbols.symb_name, unit_addr, brake_pressure, motion, marker_light, turbine, battery_cond, battery_charge, arm_status, signal_strength, verified FROM EOTRecords
        #         INNER JOIN Stations as stat on station_recorded = stat.id
        #         LEFT JOIN Symbols ON EOTRecords.symbol_id = Symbols.id \n"""
        
        # if id != -1:
        #     sql += "WHERE EOTRecords.id = :id ORDER BY EOTRecords.id Desc\n"
        # else:
        #     sql += "ORDER BY date_rec DESC\n"
        # sql += "LIMIT :results_num OFFSET :offset * :results_num"
        
        # sql_args = {"results_num": num_results, "offset": page - 1}
        # sql_args["id"] = id
    
        # resp = [row._asdict() for row in self.session.execute(text(sql), sql_args)]
        
        results = self.objs_to_dicts(self.session.execute(stmt).all())
        
        if id != -1:    
            return results
    
        count = self.get_total_record_count()

        return {
            "results": results,
            "totalPages": ceil(count / num_results),
        }
        

    def create_train_record(self, args: dict[str, Any], datetime_string: str) -> tuple[int, bool]:  #post_eot()
        """Inserts a new eot record in EOTRecords table

        Args:
            datetime_string: date and time when an eot record is created
            args: named arguments to pass into parameterized query

        Returns:
            The id of the EOT record created and the recovery request.

        Raises:
            RepositoryError if error arises in database query or argument parsing.  

        TODO: integrate this function to replace sql queries in train_history.py's post_eot() | train_history post() looks gross with parser.add_argument... how to make cleaner?
        TODO: improve documentation
        """
        recovery_request = True

        sql = """
            INSERT INTO EOTRecords (date_rec, symbol_id, station_recorded, unit_addr, brake_pressure, motion, marker_light, turbine, battery_cond, battery_charge, arm_status, signal_strength) VALUES
            (:date, :symbol_id, :station,  :unit_addr, :brake_pressure, :motion, :marker_light, :turbine, :battery_cond, :battery_charge, :arm_status, :signal_strength)
            RETURNING id
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
            if datetime_string is None:
                raise RepositoryInvalidArgumentError(
                    self.__class__.__name__,
                    message="Record timestamp must be provided!",
                    show_error=True
                )
            
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
    def get_recent_station_records(self, station_id: int) -> list[dict[str, Any]]:
        """Retrieves most recent eot records for a given station id.

        """
        from .db_core.models import Symbol, EngineNumber
        
        # sql = """
        #     SELECT * FROM EOTRecords 
        #     WHERE station_recorded = :station_id and most_recent = true 
        #     LEFT JOIN Symbols ON EOTRecords.symbol_id = Symbols.id 
        #     LEFT JOIN Engine_Numbers ON EOTRecords.engine_num = Engine_Numbers.id
        # """
        # args = {
        #     "station_id": station_id
        # }
        
        stmt = (
            select(self.model)
            .where(self.model.station_recorded == station_id)
            .where(self.model.most_recent == True)
            .join(Symbol, Symbol.id == self.model.symbol_id, isouter=True)
            .join(EngineNumber, EngineNumber.id == self.model.engine_num, isouter=True)
        )
        
        results = self.session.execute(stmt).all()
        return self.objs_to_dicts(results, {"date_rec"})
        

    # below is for eot_collation
    def get_record_collation(self, page: int, num_results: int, verified: bool | None = None) -> dict[str, list | str]:
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
                    TO_CHAR(d.date_rec, 'YYYY-MM-DD HH24:MI:SS') AS date_rec,
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
                f"Could not collate EOT records: {e}"
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
                SELECT COUNT(*) FROM UnitAddrDetails WHERE row_num = 1
            """
            
            count_sql += f"AND verified = {verified};" if verified is not None else ";"
            count = self.session.execute(text(count_sql)).scalar_one()
            
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not count EOT records: {e}"
            )

        try:
            results = {
                    "results": resp,
                    "totalPages": ceil(count / num_results)
                }
            return results
        
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not parse EOT collation results: {e}"
            )
    
    # Record/admin verification
    # def get_records_by_verification(self, page: int, verified: bool, num_results: int):
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
    #                     e.brake_pressure,
    #                     e.motion,
    #                     e.marker_light,
    #                     e.turbine,
    #                     e.battery_cond,
    #                     e.battery_charge,
    #                     e.arm_status,
    #                     e.signal_strength,
    #                     e.verified,
    #                     LAG(e.station_recorded) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) AS prev_station,
    #                     LAG(e.date_rec) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) AS prev_date_rec,
    #                     CASE
    #                         WHEN LAG(e.station_recorded) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) IS DISTINCT FROM e.station_recorded THEN 1
    #                         WHEN e.date_rec - LAG(e.date_rec) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) > INTERVAL '2 hours' THEN 1
    #                         ELSE 0
    #                     END AS is_new_group
    #                 FROM EOTRecords e
    #             ),
    #             GroupedRecords AS (
    #                 SELECT
    #                     id,
    #                     date_rec,
    #                     station_recorded,
    #                     symbol_id,
    #                     unit_addr,
    #                     brake_pressure,
    #                     motion,
    #                     marker_light,
    #                     turbine,
    #                     battery_cond,
    #                     battery_charge,
    #                     arm_status,
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
    #                     g.brake_pressure,
    #                     g.motion,
    #                     g.marker_light,
    #                     g.turbine,
    #                     g.battery_cond,
    #                     g.battery_charge,
    #                     g.arm_status,
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
    #                 d.date_rec,
    #                 d.station_name,
    #                 d.symbol_id,
    #                 d.unit_addr,
    #                 d.brake_pressure,
    #                 d.motion,
    #                 d.marker_light,
    #                 d.turbine,
    #                 d.battery_cond,
    #                 d.battery_charge,
    #                 d.arm_status,
    #                 d.signal_strength,
    #                 d.verified,
    #                 d.first_seen,
    #                 d.last_seen,
    #                 d.occurrence_count,
    #                 AGE(d.last_seen, d.first_seen) AS duration
    #             FROM UnitAddrDetails d
    #             WHERE d.row_num = 1
    #             AND d.verified = {verified_str}
    #             ORDER BY d.date_rec DESC -- Order by the most recent date
    #             LIMIT :results_num OFFSET :offset
    #         """
    #         args = {"results_num": num_results, "offset": (((page - 1) * num_results) + num_results)}
    #         resp = [row._asdict() for row in self.session.execute(text(sql), args).all()]
    #     except Exception as e:
    #         raise repository_error_translator(
    #             e, self.__class__.__name__, None,
    #             f"Could not retrieve {'verified' if verified else 'unverified'} EOT records: {e}"
    #         )

    #     try:
    #         count_sql = f"""
    #             WITH StationChanges AS (
    #                 SELECT
    #                     e.id,
    #                     e.date_rec,
    #                     e.station_recorded,
    #                     e.symbol_id,
    #                     e.unit_addr,
    #                     e.brake_pressure,
    #                     e.motion,
    #                     e.marker_light,
    #                     e.turbine,
    #                     e.battery_cond,
    #                     e.battery_charge,
    #                     e.arm_status,
    #                     e.signal_strength,
    #                     e.verified,
    #                     LAG(e.station_recorded) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) AS prev_station,
    #                     LAG(e.date_rec) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) AS prev_date_rec,
    #                     CASE
    #                         WHEN LAG(e.station_recorded) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) IS DISTINCT FROM e.station_recorded THEN 1
    #                         WHEN e.date_rec - LAG(e.date_rec) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) > INTERVAL '2 hours' THEN 1
    #                         ELSE 0
    #                     END AS is_new_group
    #                 FROM EOTRecords e
    #             ),
    #             GroupedRecords AS (
    #                 SELECT
    #                     id,
    #                     date_rec,
    #                     station_recorded,
    #                     symbol_id,
    #                     unit_addr,
    #                     brake_pressure,
    #                     motion,
    #                     marker_light,
    #                     turbine,
    #                     battery_cond,
    #                     battery_charge,
    #                     arm_status,
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
    #                     g.brake_pressure,
    #                     g.motion,
    #                     g.marker_light,
    #                     g.turbine,
    #                     g.battery_cond,
    #                     g.battery_charge,
    #                     g.arm_status,
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
    #             SELECT COUNT(*) 
    #             FROM UnitAddrDetails 
    #             WHERE row_num = 1 AND verified = {verified_str};
    #         """
    #         count = self.session.execute(text(count_sql)).scalar_one()
    #     except Exception as e:
    #         raise repository_error_translator(
    #             e, self.__class__.__name__, None,
    #             f"Could not count {'verified' if verified else 'unverified'} EOT records: {e}"
    #         )
            
    #     try:
    #         return {
    #             "results": [
    #                 {
    #                     "id": row[0],
    #                     "date_rec": row[1],
    #                     "station_name": row[2],
    #                     "symbol_id": row[3],
    #                     "unit_addr": row[4],
    #                     "brake_pressure": row[5],
    #                     "motion": row[6],
    #                     "marker_light": row[7],
    #                     "turbine": row[8],
    #                     "battery_cond": row[9],
    #                     "battery_charge": row[10],
    #                     "arm_status": row[11],
    #                     "signal_strength": row[12],
    #                     "verified": row[13],
    #                     "first_seen": row[14],
    #                     "last_seen": row[15],
    #                     "occurrence_count": str(row[16]),
    #                     "duration": str(row[17]),
    #                 }
    #                 for row in resp
    #             ],
    #             "totalPages": ceil(count[0][0] / num_results)
    #         }
    #     except Exception as e:
    #         raise repository_error_translator(
    #             e, self.__class__.__name__, None,
    #             f"Could not parse EOT verification results: {e}"
    #         )
