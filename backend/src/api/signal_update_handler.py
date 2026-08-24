from flask_restful import Resource, reqparse
from werkzeug.exceptions import BadRequest

from backend.database import db

from ..service.record_service import RecordService


class SignalUpdater(Resource):
    def put(self):
        """Updates a record's engine number and/or symbol ID based on the provided
        arguments in the request body.

        Args:
            type (int): The type of train record to update. EOT: 1, HOT: 2, DPU: 3.
            id_num (int): The ID of the record to update. Must be greater than 0.
            symbol_id (int, optional): The new symbol ID to set for the record. Must be
                greater than or equal to 0. Default: -1 (undefined)
            engi_number_id (int, optional): The new engine number ID to set for the
                record. Must be greater than or equal to 0. Default: -1 (undefined)

        Returns:
            Response: The status code of the request.
        """
        parser = reqparse.RequestParser()
        parser.add_argument("type", default=-1, type=int)
        parser.add_argument("symbol_id", default=-1, type=int)
        parser.add_argument("id_num", default=-1, type=int)
        parser.add_argument("engi_number_id", default=-1, type=int)
        args = parser.parse_args()

        # The primary key of a record must be greater than 1
        if args["id_num"] < 1:
            raise BadRequest(f"Ivalid record ID: {args["id_num"]}")
        
        # In order to update the record's fields, engine number and symbol id must also be greater than 1
        if args["engi_number_id"] < 0 and args["symbol_id"] < 0:
            raise BadRequest(
                f"Both engine [{args['engi_number_id']}] and symbol ID [{args['symbol_id']}] cannot be undefined (-1)"
            )

        # Flask creates a request-specific database session
        session = db.session
        
        # Will raise an exception if the provided record type is not valid
        service = RecordService(session, args["type"])
        service.signal_update(args["id_num"], args["symbol_id"], args["engi_number_id"])
        
        # Commit the changes of the session to the database if successful
        session.commit()
        
        return 201
    