from flask import request, jsonify
from flask_restful import Resource
from datetime import date

from src.db.trackSense_db_commands import run_exec_cmd, run_get_cmd


class StationOnline(Resource):
    def get(self):
        station = request.args.get("station_name", default=None, type=str)
        if station is None:
            return 400, {"message": "Station name not provided"}
        sql = "SELECT last_seen FROM stations WHERE station_name = %s;"
        results = run_get_cmd(sql, (station,))

        if len(results) == 0:
            return 400, {"message", "Station not found"}

        seen_date = results[0][0]

        formatted_date = seen_date.strftime("%I:%M %p") if seen_date.date() == date.today() \
            else seen_date.strftime("%b %d, %Y at %I:%M %p")

        return jsonify(
            {
                "last_seen": formatted_date
            }
        )

    def post(self):

        data = request.get_json()
        stat_id = data.get("station_id")

        sql = "UPDATE stations SET last_seen = NOW() WHERE id = %s;"

        run_exec_cmd(sql, (stat_id,))

        return 200
