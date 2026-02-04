from flask import jsonify, request
from flask_restful import Resource
from db.db import db
from service.service_core import *
from service.record_service import RecordService
from werkzeug.exceptions import BadRequest


class RecordCollation(Resource):
    """*Flask Resource* that registers the endpoints for record collation operations."""
    
    def get(self):
        """GET endpoint used to retrieve a formatted and collated collection of
        records specified by their type.
        
        Query arguments must include:
            page (int): A factor used to calculate the range of records to return in the database. 
                        Must be greater than 0.
            type (int): The type of train records to retrieve. EOT: 1, HOT: 2, DPU: 3 

        Returns:
            Response: Returns a Flask Response with a payload containing collated records of
            the provided type.
        """
        page = request.args.get("page", default=1, type=int)
        typ = request.args.get("type", default=1, type=int)
        
        # Page must be greater than zero because the window offset starts at (page - 1).
        if page <= 0:
            raise BadRequest(
                f"Invalid page argument provided: {page}. Must be greater than 0."
            )
            
        session = db.session

        # Will raise an exception if the provided record type is not valid
        record_service = RecordService(session, typ)
        
        # Retrieve and return the records using the respective record service 
        results = record_service.collate_records(page)
        return jsonify(results), 200