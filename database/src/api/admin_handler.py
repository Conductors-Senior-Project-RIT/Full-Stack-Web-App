from flask import Blueprint, abort, json, request, jsonify
from flask_restful import Resource, reqparse
from database.src.api.error_handler import MethodNotAllowedError, InvalidArgumentError
from service.record_service import RecordService
from service.service_core import *
from service.symbol_service import SymbolService
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_cors import CORS
from db.trackSense_db_commands import *

admin_bp = Blueprint("admin_bp", __name__)
CORS(admin_bp)  # Enable CORS for the admin_bp blueprint

# This class should use JWT volunteer authentication
@admin_bp.before_request
def check_auth():
    pass


@admin_bp.route("/api/add-pin", methods=["POST"])
@jwt_required()
def add_pin():
    data = request.get_json()
    lat = data.get("lat")
    lng = data.get("lng")

    if lat is None or lng is None:
        return jsonify({"message": "Invalid data"}), 400

    # Insert the pin into the database
    run_exec_cmd("INSERT INTO Pins (lat, lng) VALUES (%s, %s)", (lat, lng))
    return jsonify({"message": "Pin added successfully"}), 201


@admin_bp.route("/api/get-pins", methods=["GET"])
def get_pins():
    pins = run_get_cmd("SELECT lat, lng FROM Pins")
    return jsonify([{"lat": pin[0], "lng": pin[1]} for pin in pins])


@admin_bp.route("/symbol", methods=["GET", "POST"])
@jwt_required()
def get_symbol():
    # Retrieve the provided query parameters (if it exists)
    symbol_name = request.args.get("symbol_name", default=None, type=str)
    
    # Instantiate a symbol service
    service = SymbolService()

    if request.method == "GET":
        # The service supports an undefined symbol name and always returns a list
        results = service.get_symbol(symbol_name)
        
        # Return results in the 'results' field for consistency
        return jsonify({"results": results}), 200
    
    elif request.method == "POST":
        # To create a new symbol, a name must be provided
        if symbol_name is None:
            abort(400, "Must provide a symbol name to create a record!")

        # If a name is provided, then use the service to create a new symbol
        service.create_symbol(symbol_name)
        return 200


@admin_bp.get("/record_verifier")
@jwt_required()
def get_records():
    page = request.args.get("page", default=1, type=int)
    typ = request.args.get("type", default=-1, type=int)
    
    if page < 1:
        abort(400, f"Invalid page number: {page}")
    
    record_service = RecordService(typ)
    results = record_service.get_unverified_records(page)
    return jsonify(results), 200


@admin_bp.post("/record_verifier")
@jwt_required()
def post_record():
    parser = reqparse.RequestParser()
    parser.add_argument("id", type=int, default=-1)
    parser.add_argument("type", type=int, default=-1)
    parser.add_argument("symbol", type=int, default=-1)
    parser.add_argument("engine_number", type=int, default=-1)
    args = parser.parse_args()
        
    arg_validators = {
        "record ID": args.id,
        "symbol ID": args.symbol,
        "engine number": args.engine_number
    }
    
    for arg, val in arg_validators.items():
        if val < 1:
            abort(400, f"{arg} must be greater than 1, given: {val}")
        
    record_service = RecordService(args.type)
    record_service.verify_record(args.id, args.symbol, args.engine_number)
    return 200
