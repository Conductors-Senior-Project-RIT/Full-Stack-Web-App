from flask import request
from flask_restful import Resource
from backend.database import db
from ..service.record_service import RecordService
from werkzeug.exceptions import BadRequest


class RecordCollation(Resource):
    """Flask `Resource` that registers the endpoints for record collation operations."""
    
    def get(self):
        """
        GET endpoint used to retrieve a paginated collation of train records grouped by
        unit address and station. Groups are formed when either the station changes or a
        duration of more than 2 hours elapses between records. Returns the most recent
        record per group along with aggregate information such as `first_seen`,
        `last_seen`, `occurrence_count`, and `duration`.

        Args:
            page (int): A factor used to calculate the range of records to return in the
                database. Must be greater than 0. Default: 1
            type (int): The type of train records to retrieve. EOT: 1, HOT: 2, DPU: 3.
                Default: 1

        Returns:
            Response: Returns a Flask Response with a payload containing collated
                records of the provided type. See `backend/docs/api.md` for more details
                on the response format.
        """
        page = request.args.get("page", default=1, type=int)
        typ = request.args.get("type", default=1, type=int)
        
        # Page must be greater than zero because the window offset starts at (page - 1).
        if page <= 0:
            raise BadRequest(
                f"Invalid page argument provided: {page}. Must be greater than 0."
            )
            
        # Flask creates a request-specific database session
        session = db.session
        
        # Will raise an exception if the provided record type is not valid
        record_service = RecordService(session, typ)
        results = record_service.get_collated_records(page)
        
        # The service already returns a JSON-serializable response, so just return the result
        return results, 200