from math import ceil
from typing import Any
from sqlalchemy import desc, func, select, text

from .db_core.models import EOTRecord
from .base_record_repo import RecordRepository
from .db_core.exceptions import (
    repository_error_translator,
    repository_error_handler,
)


class EOTRepository(RecordRepository[EOTRecord]):
    """A database interface for EOT record querying.

    This class implements EOT-specific querying logic for the abstract methods in
    `RecordRepository`, while also maintaining compatiblity with its conrete methods.
    Since `RecordRepository` inherits functionality from `BaseRepository`, this class
    also supports CRUD functionality with `EOTRecord`.

    Args:
        RecordRepository (EOTRecord): Extends the behavior of `RecordRepository` for
            `EOTRecord`.
    """

    def __init__(self, session):
        """Constructor for a repository that interacts with EOT train records.

        An `EOTRepository` can be instantiated through the `get_record_repository`
        function in `record_types` with a value of either `1` or `RecordTypes.EOT`.

        Args:
            session (Session): Specifies the database session in which the repository
                operates. Each function that makes changes within a session flushes all
                units of work. It is the job of higher layers to commit or rollback any
                changes in the session.
        """
        super().__init__(EOTRecord, session, "EOT Record", "eot")

    # Below is train_history.py related
    @repository_error_handler()
    def get_train_history(self, id: int) -> dict[str, Any]:
        """Returns an EOT record as a dictionary containing the following columns and their
        respective values: `id, date_rec, station_name, unit_addr, brake_pressure,
        motion, marker_light, turbine, battery_cond, battery_charge, arm_status,
        signal_strength, verified`.

        Args:
            id (int): A value corresponding to a record's primary key.

        Returns:
            dict[str, Any]: If the operation is successful, a dictonary is returned
                containining the specific columns and values for a given record.
        """
        from .db_core.models import Station, Symbol

        stmt = (
            select(
                self.model.id,
                func.to_char(self.model.date_rec, "YYYY-MM-DD HH24:MI:SS").label(
                    "date_rec"
                ),
                Station.station_name,
                Symbol.symb_name,
                self.model.unit_addr,
                self.model.brake_pressure,
                self.model.motion,
                self.model.marker_light,
                self.model.turbine,
                self.model.battery_cond,
                self.model.battery_charge,
                self.model.arm_status,
                self.model.signal_strength,
                self.model.verified,
            )
            .join(Station, Station.id == self.model.station_recorded)
            .outerjoin(Symbol, Symbol.id == self.model.symbol_id)
            .where(self.model.id == id)
            .order_by(desc(self.model.id))
        )

        results = self.session.execute(stmt).one_or_none()
        return self.objs_to_dicts(results)

    # Below is station_handler.py related
    def get_recent_station_records(self, station_id: int) -> list[dict[str, Any]]:
        """Retrieves most recent EOT records from a station with a matching station id.

        Args:
            station_id (int): The ID of a station which defines which HOT records to
                retrieve.

        Returns:
            list[dict[str, Any]]: A list of HOT records respresented as dictionaries
                that have a matching station ID.
        """
        from .db_core.models import Symbol, EngineNumber

        stmt = (
            select(self.model)
            .where(self.model.station_recorded == station_id)
            .where(self.model.most_recent.is_(True))
            .join(Symbol, Symbol.id == self.model.symbol_id, isouter=True)
            .join(EngineNumber, EngineNumber.id == self.model.engine_num, isouter=True)
        )

        results = self.session.execute(stmt).all()
        return self.objs_to_dicts(
            results, {"date_rec"}
        )  # Convert 'date_rec' to a string.

    # below is for eot_collation
    def get_record_collation(
        self, page: int, num_results: int, verified: bool | None = None
    ) -> dict[str, list | int]:
        """Retrieves a paginated collation of EOT records grouped by unit address and
        station.

        Executes a multi-stage SQL query that groups EOT records by unit address and
        station, where a new group is formed when either the station changes or a
        duration of more than 2 hours occurs between records. Returns the most recent
        record per group along with aggregate details such as `first_seen`, `last_seen`,
        `occurrence_count`, and `duration`. A second query retrieves the total count of
        grouped records for pagination. Optionally filters results by verification
        status if provided.

        The following columns are returned for each record: `id, date_rec, station_name,
        symb_name, unit_addr, brake_pressure, motion, marker_light, turbine,
        battery_cond, battery_charge, arm_status, signal_strength, verified, first_seen,
        last_seen, occurrence_count, duration, locomotive_num`.

        Args:
            page (int): The page number to retrieve, 1-indexed.
            num_results (int): The number of results to return per page.
            verified (bool | None): If True or False, filters records by their
                `verified` status. If None, no filter is applied. Defaults to None.

        Returns:
            dict[str, list | int]: A dictionary containing: 
                - `results` (list[dict]): The paginated and collated HOT records as 
                    dictionaries. 
                - `totalPages` (int): The total number of pages based on `num_results`.

        Raises:
            `RepositoryError`: If any stage of the query, count, or result parsing
                    fails.
        """

        try:
            # This query performs the aggregation step described in the doc comment above.
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

            # Return only verified or unverified records if specified
            if verified is not None:
                sql += f"AND verified = {verified}"

            # Order by descending order, and limit the results with a page offset
            sql += """
                ORDER BY d.date_rec DESC
                LIMIT :results_num OFFSET :offset
            """
            args = {"results_num": num_results, "offset": (page - 1) * num_results}
            results = self.session.execute(text(sql), args).all()

            # Convert the results to dictionaries and convert duration and occurrence_count to strings
            resp = self.objs_to_dicts(results, {"duration", "occurrence_count"})

        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None, f"Could not collate EOT records: {e}"
            )

        try:
            # The original team used this to count the records, but there should be an easier way to do this.
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
                e, self.__class__.__name__, None, f"Could not count EOT records: {e}"
            )

        try:
            results = {"results": resp, "totalPages": ceil(count / num_results)}
            return results

        except Exception as e:
            raise repository_error_translator(
                e,
                self.__class__.__name__,
                None,
                f"Could not parse EOT collation results: {e}",
            )
