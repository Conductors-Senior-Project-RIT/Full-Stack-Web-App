from flask import jsonify
from flask_restful import Resource, reqparse

from backend.db import db
from service.record_service import RecordService


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

        if args["id_num"] < 1:
            return jsonify({"error": f"Ivalid record ID: {args["id_num"]}"}), 400
        
        if args["engi_number_id"] == -1 and args["symbol_id"] == -1:
            return jsonify(
                {"error": f"Both engine [{args['engi_number_id']}] and symbol ID [{args['id_num']}] cannot be undefined (-1)"}
            ), 400

        # Ensure that a valid record type, a valid record ID, and at least
        # a valid engine number or symbol ID is provided.
        session = db.session
        
        service = RecordService(session, args["type"])
        service.signal_update(args["id_num"], args["symbol_id"], args["engi_number_id"])
        return 200
    