from flask import request, jsonify
from flask_restful import Resource
from werkzeug.exceptions import BadRequest

from service.service_core import ServiceTimeoutError, ServiceInternalError, ServiceResourceNotFound
from service.station_service import StationService
from db.db import db

class StationOnline(Resource):
    def get(self):
        station = request.args.get("station_name", default=None, type=str)
        if station is None:
            raise BadRequest("Station name not provided!")

        session = db.session

        formatted_date = StationService(session).get_last_seen(station)
        return jsonify({"last_seen": formatted_date}), 200
    

    def put(self):
        data = request.get_json()
        stat_id = int(data.get("station_id"))
        
        if stat_id < 1:
            raise BadRequest(f"Station ID must be greater than or equal to 1 but ({stat_id}) was provided!")

        session = db.session

        StationService(session).update_last_seen(stat_id)
        return 200