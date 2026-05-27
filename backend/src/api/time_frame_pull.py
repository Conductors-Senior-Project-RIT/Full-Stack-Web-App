import re

from flask import request
from flask_restful import Resource
from werkzeug.exceptions import BadRequest
from ..service.record_service import RecordService
from backend.database import db

class RecentActivities(Resource):
    def get(self):
        """Returns records at a provided station within a specified timeframe. The
        specified time range serves as a lower bound, while the time the request was
        received serves as an upper bound.

        Args:
            type (int, optional): The type of the records that are being retrieved. EOT:
                1, HOT: 2, DPU: 3. Currently, DPU is not supported. If no type is
                provided, records of all types are returned.
            station_id (int, optional): The ID associated with a station used to
                retrieve the records it has recorded. If this field is not provided,
                `station_name` must be provided as a parameter.
            timerange (str): Delta time that defines the range records should be pulled
                from. Format: `HH:MM:SS`
            most_recent (bool, optional): A boolean that determines if the most recent
                records should be retrieved (where `most_recent` is True in database).
                Default: True
            station_name (str, optional): If `station_id` is not provided, the name of
                the station can be used to retrieve records; however, in that case, this
                field is required.

        Raises:
            `BadRequest`: Raised if the time range is not provided or is an invalid
                    format.

        Returns:
            Response: Returns a JSON object containing the records that were recorded at
                the specified station within the provided time range. If no records
                match the query, an empty array is returned.
        """
        typ = request.args.get("type", default=None, type=int)
        stat_id = request.args.get("station_id", default=-1, type=int)
        time_range = request.args.get("timerange", default=None, type=str)
        recent = request.args.get("most_recent", default=True, type=bool)
        station = request.args.get("station_name", default=None, type=str)

        # Check if time range is provided and matches the following format: HH:MM:SS
        if time_range is None or re.match(r"(\d{2}:){2}\d{2}", time_range) is None:
            raise BadRequest("A time range must be provided in the following format: HH:MM:SS")

        # Create a request-specific database session
        session = db.session
        
        # If type is not provided, the service pulls from all repositories
        record_service = RecordService(session, typ)
        results = record_service.time_frame_pull(
            time_range, recent, stat_id, station
        )
        
        # The service already returns a JSON-serializable response, so just return the result
        return results, 200
    

