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

        # It is clear that the primary key of a record must be greater than 1
        if args["id_num"] < 1:
            raise BadRequest(f"Ivalid record ID: {args["id_num"]}")
        
        # In order to update the record's fields, engine number and symbol id must be greater than 1
        if args["engi_number_id"] < 0 and args["symbol_id"] < 0:
            raise BadRequest(
                f"Both engine [{args['engi_number_id']}] and symbol ID [{args['id_num']}] cannot be undefined (-1)"
            )

        # Flask creates a request-specific database session
        session = db.session
        
        # Will raise an exception if the provided record type is not valid
        service = RecordService(session, args["type"])
        
        # Update the symbol id and engine number if valid
        service.signal_update(args["id_num"], args["symbol_id"], args["engi_number_id"])
        
        # Commit the changes of the session to the database if successful
        session.commit()
        
        return 201
    