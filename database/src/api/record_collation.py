from flask import jsonify, request
from flask_restful import Resource
from service.service_core import *
from service.record_service import RecordService

RESULTS_NUM = 250


class RecordCollation(Resource):
    def get(self):
        page = request.args.get("page", default=1, type=int)
        typ = request.args.get("type", default=-1, type=int)
        
        try:
            record_service = RecordService(typ)
            results = record_service.collate_records(page)
            return jsonify(results), 200
        except ServiceInvalidArgument as e:
            return jsonify({"error": str(e)}), 400
        except ServiceTimeoutError:
            return jsonify({"error", "Request timed out!"}), 408
        except ServiceInternalError as e:
            return jsonify({"error", str(e)}), 500