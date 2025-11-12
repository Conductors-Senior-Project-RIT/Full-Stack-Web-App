from flask import jsonify
from flask_restful import Resource, reqparse
import json, datetime, requests

from db.eot_db import update_eot_symbol, update_eot_engine_num
from db.hot_db import update_hot_symbol, update_hot_engine_num
from record_types import RecordTypes


class SignalUpdater(Resource):
    def post(self):
        """Updates a record's engine number and/or symbol ID based on the provided arguments in the request body.

        Returns:
            int: The status code of the request.
        """
        parser = reqparse.RequestParser()
        parser.add_argument("type", default=-1, type=int)
        parser.add_argument("symbol_id", default=-1, type=int)
        parser.add_argument("id_num", default=-1, type=int)
        parser.add_argument("engi_number_id", default=-1, type=int)
        args = parser.parse_args()

        # Ensure that a valid record type, a valid record ID, and at least
        # a valid engine number or symbol ID is provided.
        if (
            not RecordTypes.has_value(args["type"])
            or args["id_num"] == -1
            or (args["engi_number_id"] == -1 and args["symbol_id"] == -1)
        ):
            # Invalid arguments provided
            print("bad request")
            return 400
        
        # The symbol and engine update functions are stored in a dictionary that can easily be executed via record type
        symbol_update_funcs = {
            RecordTypes.EOT.value: lambda i,s: update_eot_symbol(i, s),
            RecordTypes.HOT.value: lambda i,s: update_hot_symbol(i, s),
            RecordTypes.DPU.value: lambda _: print("DPU not implemented!")
        }
        
        engine_num_update_funcs = {
            RecordTypes.EOT.value: lambda i,e: update_eot_engine_num(i, e),
            RecordTypes.HOT.value: lambda i,e: update_hot_engine_num(i, e),
            RecordTypes.DPU.value: lambda _: print("DPU not implemented!")
        }

        # Execute our update functions if a valid symbol and/or engine number is provided
        if args["symbol_id"] != -1:
            symbol_update_funcs[args["type"]](args["id_num"], args["symbol_id"])

        if args["engi_number_id"] != -1:
            engine_num_update_funcs(args["type"])(args["id_num"], args["engi_number_id"])

        return 200