from flask import jsonify
from flask_restful import Resource, reqparse
from db.trackSense_db_commands import *
import json, datetime


class HistoryDB(Resource):
    def get(self):
        sql = """
        SELECT EOTRecords.id, date_rec, station_recorded, symbol_id, unit_addr, brake_pressure, motion, marker_light, turbine, battery_cond, battery_charge, arm_status, signal_stength, verified FROM EOTRecords
        INNER JOIN Symbols as sym on symbol_id = sym.id
        INNER JOIN Stations as stat on station_recorded = stat.id
        """
        resp = run_get_cmd(sql)
        print(resp)
        return jsonify(
            [
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
        )
        # print('get goes here!')
        # return

    def post(self):
        # print('post goes here!')
        date_rec = datetime.datetime.now()
        dt_str = date_rec.strftime("%Y-%m-%d %H:%M:%S")
        parser = reqparse.RequestParser()
        parser.add_argument("type", default=-1, type=int)
        parser.add_argument("station_id", default=0, type=int)
        parser.add_argument("symbol_id", type=str, default=0)
        parser.add_argument("unit_addr", type=str, default="UNKNOWN")
        parser.add_argument("brake_pressure", type=str, default="UNKNOWN")
        parser.add_argument("motion", type=str, default="UNKNOWN")
        parser.add_argument("marker_light", type=str, default="UNKNOWN")
        parser.add_argument("turbine", type=str, default="UNKNOWN")
        parser.add_argument("battery_cond", type=str, default="UNKNOWN")
        parser.add_argument("battery_charge", type=str, default="UNKNOWN")
        parser.add_argument("arm_status", type=str, default="UNKNOWN")
        parser.add_argument("signal_strength", type=float, default=0.0)
        parser.add_argument("frame_sync", type=str, default="UNKNOWN")
        parser.add_argument("command", type=str, default="UNKNOWN")
        parser.add_argument("checkbits", type=str, default="UNKNOWN")
        parser.add_argument("parity", type=str, default="UNKNOWN")
        args = parser.parse_args()
        # right now this has 0 authentication. Too bad!

        # type --> 1 = EOT, 2 = HOT, 3 = DPU
        if type == 1:
            sql = """
                INSERT INTO EOTRecords (date_rec, symbol_id, station_recorded, unit_addr, brake_pressure, motion, marker_light, turbine, battery_cond, battery_charge, arm_status, signal_stength) VALUES
                (%(date)s, %(symbol_id)s, %(station)s,  %(unit_addr)s, %(brake_pressure)s, %(motion)s, %(marker_light)s, %(turbine)s, %(battery_cond)s, %(battery_charge)s, %(arm_status)s, %(signal_strength)s)
            """
            sql_args = {
                "date": dt_str,
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
                "symbol_id": args["symbol_id"],
            }
            resp = run_exec_cmd(sql, sql_args)
            # print(resp.statusmessage)
            # print(run_get_cmd('SELECT * FROM EOTRecords'))
        elif type == 2:
            sql_args = {
                "date": dt_str,
                "station": args["station_id"],
                "frame_sync": args["frame_sync"],
                "command": args["command"],
                "checkbits": args["checkbits"],
                "parity": args["parity"],
                "unit_addr": args["unit_addr"],
            }

            sql = """
                INSERT INTO HOTRecords (date_rec, station_recorded, frame_sync, unit_addr, command, checkbits, parity) VALUES
                (%(date)s, %(station)s, %(frame_sync)s, %(unit_addr)s, %(command)s, %(checkbits)s, %(parity)s)
            """
            resp = run_exec_cmd(sql, sql_args)
            return
        elif type == 3:
            return
        else:
            print("something is bad in the request")
            return 400
        return 200

    def delete(self):  # not sure if this is needed
        print("delete goes here!")
        return

    def put(self):  # this will be needed, not sure how to implement this yet
        print("put goes here!")
        return
