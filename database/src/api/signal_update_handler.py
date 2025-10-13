from flask import jsonify
from flask_restful import Resource, reqparse
from db.trackSense_db_commands import *
import json, datetime, requests

from db.trackSense_db_commands import run_exec_cmd, run_get_cmd


class SignalUpdater(Resource):

    def post(self):
        resp = None
        parser = reqparse.RequestParser()
        parser.add_argument("type", default=-1, type=int)
        parser.add_argument("symbol_id", default=-1, type=int)
        parser.add_argument("id_num", default=-1, type=int)
        parser.add_argument("engi_number_id", default=-1, type=int)
        args = parser.parse_args()

        if (
            args["type"] <= 0
            or args["type"] > 2
            or args["id_num"] == -1
            or (args["engi_number_id"] == -1 and args["symbol_id"] == -1)
        ):
            print("bad request")
            return 400

        if args["symbol_id"] != -1:

            sql_args = {
                "id": args["id_num"],
                "symbol_id": args["symbol_id"],
                "engine_id": args["engi_number_id"],
            }

            if args["type"] == 1:
                sql_update = """
                        UPDATE EOTRecords
                        SET symbol_id = %(symbol_id)s 
                        WHERE id = %(id)s
                        """

            if args["type"] == 2:
                sql_update = """
                        UPDATE HOTRecords
                        SET symbol_id = %(symbol_id)s 
                        WHERE id = %(id)s
                        """

            resp = run_exec_cmd(sql_update, sql_args)
            print(resp)

        if args["engi_number_id"] != -1:

            sql_args = {"id": args["id_num"], "engine_id": args["engi_number_id"]}

            sql_update = ""

            if args["type"] == 1:
                sql_update = """
                                UPDATE EOTRecords
                                SET engine_num = %(engine_id)s 
                                WHERE id = %(id)s
                                """

            if args["type"] == 2:
                sql_update = """
                                UPDATE HOTRecords
                                SET engine_num = %(engine_id)s  
                                WHERE id = %(id)s
                                """

            resp = run_exec_cmd(sql_update, sql_args)
            print(resp)

        return 200
