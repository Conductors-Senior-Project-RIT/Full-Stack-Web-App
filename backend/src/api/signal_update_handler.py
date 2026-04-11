from flask_restful import Resource, reqparse
from werkzeug.exceptions import BadRequest

from backend.database import db
from ..service.record_service import RecordService


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
            raise BadRequest(f"Ivalid record ID: {args["id_num"]}")
        
        if args["engi_number_id"] == -1 and args["symbol_id"] == -1:
            raise BadRequest(
                f"Both engine [{args['engi_number_id']}] and symbol ID [{args['id_num']}] cannot be undefined (-1)"
            )


        # Ensure that a valid record type, a valid record ID, and at least
        # a valid engine number or symbol ID is provided.
        session = db.session
        service = RecordService(session, args["type"])
        service.signal_update(args["id_num"], args["symbol_id"], args["engi_number_id"])
        session.commit()
        
        return 201
    