from flask import jsonify, request
from flask_restful import Resource, reqparse
from db.trackSense_db_commands import *
from math import ceil

RESULTS_NUM = 250


class DataCollation(Resource):
    def get(self):
        page = request.args.get("page", default=1, type=int)

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
        )
