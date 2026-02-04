from flask import request, jsonify
from flask_restful import Resource
from datetime import date

from database.src.service.service_core import ServiceTimeoutError, ServiceInternalError, ServiceResourceNotFound
from database.src.service.station_service import StationService
from db.trackSense_db_commands import run_exec_cmd, run_get_cmd
from db.db import db

class StationOnline(Resource):
    def get(self):
        try:
            station = request.args.get("station_name", default=None, type=str)
            if station is None:
                return jsonify({"message": "Station name not provided"}), 400

            session = db.session

            formatted_date = StationService(session).get_last_seen(station)
            return jsonify({"last_seen": formatted_date}), 200
        
        except ServiceTimeoutError:
            return ({"error": "Request timed out!"}), 408
        except ServiceInternalError as e:
            return ({"error": str(e)}), 500
        except ServiceResourceNotFound as e:
            return ({"error": str(e)}), 404

    def put(self):
        try:
            data = request.get_json()
            stat_id = int(data.get("station_id"))
            
            if stat_id < 1:
                raise ValueError()

            session = db.session

            StationService(session).update_last_seen(stat_id)
            return 200
        
        except (ValueError, TypeError, MemoryError, OverflowError):
            return ({"error": "Invalid station ID!"}), 400
        except ServiceTimeoutError:
            return ({"error": "Request timed out!"}), 408
        except ServiceInternalError as e:
            return ({"error": str(e)}), 500
        except ServiceResourceNotFound as e:
            return ({"error": str(e)}), 404