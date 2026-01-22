from flask import jsonify, request
from flask_restful import Resource
from src.db.trackSense_db_commands import *
from math import ceil

RESULTS_NUM = 250


class HotCollation(Resource):
    def get(self):
        page = request.args.get("page", default=1, type=int)

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
        return jsonify(
            {
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
        )