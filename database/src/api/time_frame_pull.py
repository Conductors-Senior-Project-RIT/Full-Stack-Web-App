from email.policy import default

from flask import jsonify, request
from flask_restful import Resource, reqparse
from db.trackSense_db_commands import *
import json, datetime, requests


class recent_activities(Resource):
    # expects time as hours:minutes:seconds
    def get(self):
        """
        parser = reqparse.RequestParser()
        parser.add_argument("type", default=-1, type=int)
        parser.add_argument("station_id", default=-1, type=int)
        parser.add_argument("timerange", default=None, type=str)
        parser.add_argument("most_recent", default=True, type=bool)
        parser.add_argument("station_name", default=None, type=str)
        args = parser.parse_args()
        """

        parser = reqparse.RequestParser()
        typ = request.args.get("type", default=-1, type=int)
        id = request.args.get("station_id", default=-1, type=int)
        time_range = request.args.get("timerange", default=None, type=str)
        recent = request.args.get("most_recent", default=True, type=bool)
        station = request.args.get("station_name", default=None, type=str)

        if typ != 1 and typ != 2 and typ != 3:
            print("Bad request")
            return 400

        if time_range == None:
            print("Bad request")
            return 400

        time_increments = time_range.split(":")

        curr_date = datetime.datetime.now()
        delta = datetime.timedelta(
            hours=int(time_increments[0]),
            minutes=int(time_increments[1]),
            seconds=int(time_increments[2]),
        )
        altered_time = curr_date - delta
        dt_str = altered_time.strftime("%Y-%m-%d %H:%M:%S")
        # id = args["station_id"]
        # recent = args["most_recent"]

        # station = args["station_name"]
        stat_id = -1
        if station:
            sql_args = {"station_name": station}
            temp = run_get_cmd(
                "SELECT id FROM Stations WHERE station_name = %(station_name)s",
                (sql_args),
            )
            if len(temp) != 0:
                stat_id = temp[0][0]

        if stat_id == -1:
            stat_id = id

        print(dt_str)
        print(station)
        print(stat_id)
        symbs = run_get_cmd("SELECT * FROM Symbols")
        print(symbs)
        if typ == 1:
            resp = self.eot_sql_helper(stat_id, dt_str, recent)

            return jsonify(
                [
                    {
                        "eot_id": tup[0],
                        "eot_unit_addr": tup[1],
                        "eot_date_rec": str(tup[2].time())[0:5],
                        "eot_station_name": tup[3],
                        "eot_symbol_id": run_get_cmd(
                            "SELECT symb_name FROM Symbols WHERE id = %(symid)s",
                            {"symid": tup[4]},
                        ),
                        "eot_engine_num_id": tup[5],
                    }
                    for tup in resp
                ]
            )
        if typ == 2:
            resp = self.hot_sql_helper(stat_id, dt_str, recent)
            return jsonify(
                [
                    {
                        "hot_id": tup[0],
                        "hot_unit_addr": tup[1],
                        "hot_date_rec": (str(tup[2].time())[0:5]),
                        "hot_station_name": tup[3],
                        "hot_symbol_id": run_get_cmd(
                            "SELECT symb_name FROM Symbols WHERE id = %(symid)s",
                            {"symid": tup[4]},
                        ),
                        "hot_engine_num_id": tup[5],
                    }
                    for tup in resp
                ]
            )
        if typ == 3:
            resp_1 = self.eot_sql_helper(stat_id, dt_str, recent)
            resp_2 = self.hot_sql_helper(stat_id, dt_str, recent)
            final_resp = []
            for tup in resp_1:
                final_resp.append(
                    {
                        "id": tup[0],
                        "unit_addr": tup[1],
                        "date_rec": str(tup[2].time())[0:5],
                        "station_name": tup[3],
                        "symbol_id": run_get_cmd(
                            "SELECT symb_name FROM Symbols WHERE id = %(symid)s",
                            {"symid": tup[4]},
                        ),
                        "engine_num_id": tup[5],
                        "Data_type": "EOT",
                    }
                )
            for tup in resp_2:
                final_resp.append(
                    {
                        "id": tup[0],
                        "unit_addr": tup[1],
                        "date_rec": (str(tup[2].time())[0:5]),
                        "station_name": tup[3],
                        "symbol_id": run_get_cmd(
                            "SELECT symb_name FROM Symbols WHERE id = %(symid)s",
                            {"symid": tup[4]},
                        ),
                        "engine_num_id": tup[5],
                        "Data_type": "HOT",
                    }
                )
            # print("final resp:" , final_resp)
            # print(final_resp[0])
            # sorted_resp = sorted(final_resp,key=lambda d: d["date_rec"])
            final_resp.sort(key=lambda x: x["date_rec"], reverse=True)
            # print("sorted resp: " , final_resp)
            return final_resp

    def eot_sql_helper(self, id, dt_str, recent):
        if id == -1:

            sql = """
                    SELECT EOTRecords.id, unit_addr, date_rec, stat.station_name, symbol_id, engine_num FROM EOTRecords
                    INNER JOIN Stations as stat on station_recorded = stat.id
                    WHERE date_rec >= %(date_stamp)s 
                    """
            if recent:
                sql += " AND most_recent = TRUE"
            sql_args = {"date_stamp": dt_str}
            resp = run_get_cmd(sql, sql_args)
            return resp
        else:
            sql = """
                    SELECT EOTRecords.id, unit_addr, date_rec, stat.station_name, symbol_id, engine_num, locomotive_num FROM EOTRecords
                    INNER JOIN Stations as stat on station_recorded = stat.id
                    WHERE date_rec >= %(date_stamp)s 
                    AND stat.id = %(station_id)s
                    """
            if recent:
                sql += " AND most_recent = TRUE"
            sql_args = {"date_stamp": dt_str, "station_id": id}

            resp = run_get_cmd(sql, sql_args)
            print(resp)
            return resp

    def hot_sql_helper(self, id, dt_str, recent):

        if id == -1:

            sql = """
                    SELECT HOTRecords.id, unit_addr, date_rec, stat.station_name, symbol_id, engine_num, locomotive_num FROM HOTRecords
                    INNER JOIN Stations as stat on station_recorded = stat.id
                    WHERE date_rec >= %(date_stamp)s 
                    """
            if recent:
                sql += " AND most_recent = TRUE"
            sql_args = {"date_stamp": dt_str}

            resp = run_get_cmd(sql, sql_args)
            print(resp)
            return resp
        else:
            sql = """
                    SELECT HOTRecords.id, unit_addr, date_rec, stat.station_name, symbol_id, engine_num FROM HOTRecords
                    INNER JOIN Stations as stat on station_recorded = stat.id
                    WHERE date_rec >= %(date_stamp)s 
                    AND stat.id = %(station_id)s
                    """
            if recent:
                sql += " AND most_recent = TRUE"
            sql_args = {"date_stamp": dt_str, "station_id": id}

            resp = run_get_cmd(sql, sql_args)
            print(resp)
            return resp
