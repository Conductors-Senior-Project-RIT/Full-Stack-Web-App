from flask import jsonify, request
from flask_restful import Resource, reqparse
from service.record_service import RecordService
from service.service_core import *


class RecordVerifier(Resource):
    def get(self):

        page = request.args.get("page", default=1, type=int)
        typ = request.args.get("type", default=-1, type=int)
        
        if page < 1:
            return jsonify({"error", f"Invalid page number: {page}"}), 400
        
        try:
            record_service = RecordService(typ)
            results = record_service.get_unverified_records(page)
            return jsonify(results), 200
        except ServiceInvalidArgument as e:
            return jsonify({"error": str(e)}), 400
        except ServiceTimeoutError:
            return jsonify({"error": "Request timed out!"}), 408
        except ServiceInternalError as e:
            return jsonify({"error": str(e)}), 500


    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, default=-1)
        parser.add_argument("type", type=int, default=-1)
        parser.add_argument("symbol", type=int, default=-1)
        parser.add_argument("engine_number", type=int, default=-1)
        args = parser.parse_args()

        
        arg_validators = {
            "record ID": args["id"],
            "symbol ID": args["symbol"],
            "engine number": args["engine_number"]
        }
        
        for arg, val in arg_validators.items():
            if val < 1:
                return jsonify(
                    {"error": f"Invalid argument, {arg} must be greater than 1, given: {val}"}
                ), 400
                
        try:
            record_service = RecordService(args["type"])
            record_service.verify_record(args["id"], args["symbol"], args["engine_number"])
            return 200
        
        except ServiceInvalidArgument as e:
            return jsonify({"error": str(e)}), 400
        except ServiceResourceNotFound as e:
            return jsonify({"error", str(e)}), 404
        except ServiceTimeoutError:
            return jsonify({"error": "Request timed out!"}), 408
        except ServiceInternalError as e:
            return jsonify("error", str(e)), 500
