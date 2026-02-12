
from flask import jsonify, request
from flask_restful import Resource
from werkzeug.exceptions import BadRequest
from service.record_service import RecordService
from backend.db import db

class recent_activities(Resource):
    # expects time as hours:minutes:seconds
    def get(self):
        """
        parser = reqparse.RequestParser()
        parser.add_argument("type", default=-1, type=int)
        parser.add_argument("station_id", default=-1, type=int)
        parser.add_argument("timerange", default=None, type=str)
        parser.add_argument("most_recent", default=True, type=bool)
        parser.add_argument("station_name", default=None, type=str)
        args = parser.parse_args()
        """

        typ = request.args.get("type", default=-1, type=int)
        stat_id = request.args.get("station_id", default=-1, type=int)
        time_range = request.args.get("timerange", default=None, type=str)
        recent = request.args.get("most_recent", default=True, type=bool)
        station = request.args.get("station_name", default=None, type=str)

        if time_range == None:
            raise BadRequest("Invalid time range!")

        session = db.session
        
        record_service = RecordService(session, None)
        results = record_service.time_frame_pull(
            time_range, recent, stat_id, station
        )
        return jsonify(results), 200

