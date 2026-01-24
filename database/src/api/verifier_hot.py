from flask import jsonify, request
from flask_restful import Resource, reqparse
from db.trackSense_db_commands import *
from math import ceil


class LogVerifierHOT(Resource):

    LIMIT_NUM = 250

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
        AND d.verified = false
        ORDER BY d.unit_addr, d.date_rec DESC
        LIMIT %(results_num)s OFFSET %(offset)s * %(results_num)s
        """
        args = {"results_num": self.LIMIT_NUM, "offset": page - 1}
        count_sql = """SELECT COUNT(*) FROM HOTRecords
        WHERE verified = false
        """
        count = run_get_cmd(count_sql)
        resp = run_get_cmd(sql, args)
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
                        "first_seen": tup[7],
                        "last_seen": tup[8],
                        "occurrence_count": tup[9],
                        "duration": str(tup[10]),
                    }
                    for tup in resp
                ],
                "totalPages": ceil(count[0][0] / self.LIMIT_NUM),
            }
        )

    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, default="NONE")
        parser.add_argument("symbol", type=int, default="NONE")
        parser.add_argument("engine_number", type=str, default="NONE")

        args = parser.parse_args()
        sql_args = {
            "id": args["id"],
            "symbol": args["symbol"],
            "engine_num": args["engine_number"],
        }

        sql = """
            UPDATE HOTRecords
            SET symbol_id = %(symbol)s, 
            locomotive_num = %(engine_num)s,
            verified = true
            WHERE id = %(id)s
        """

        run_exec_cmd(sql, sql_args)