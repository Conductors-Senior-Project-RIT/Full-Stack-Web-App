from flask import Blueprint, abort, request, jsonify
from flask_restful import reqparse
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from flask_cors import CORS
from werkzeug.exceptions import Unauthorized
from service.record_service import RecordService
from service.service_core import *
from service.symbol_service import SymbolService
from db.trackSense_db_commands import *
from database.src.db.db import db


volunteer_bp = Blueprint("volunteer_bp", __name__)
CORS(volunteer_bp)  # Enable CORS for the volunteer_bp blueprint


@volunteer_bp.before_request
def check_jwt_auth():
    """Before a request is made to any route in this blueprint, this function checks 
    whether the request includes a JWT with sufficient user privileges.

    Raises:
        Unauthorized: An exception will be raised if the user role is not provided or if it does not have
        the necessary user privileges.
    """
    # Verify that a JWT was provided
    verify_jwt_in_request()
    
    # Access the set of additional claims created with JWT
    claims = get_jwt()
    # Obtain user's role from JWT if exists
    user_role = claims.get("user_role")
    
    # If user role is not present in claims, None is returned (error in authentication)
    if user_role is None:
        raise Unauthorized("User role undefined!")
    
    # Check if user unauthorized, not volunteer (1) or admin (0)
    if user_role > 1:
        raise Unauthorized("User is not permitted!")


@volunteer_bp.route("/api/add-pin", methods=["POST"])
def add_pin():
    data = request.get_json()
    lat = data.get("lat")
    lng = data.get("lng")

    if lat is None or lng is None:
        return jsonify({"message": "Invalid data"}), 400

    # Insert the pin into the database
    run_exec_cmd("INSERT INTO Pins (lat, lng) VALUES (%s, %s)", (lat, lng))
    return jsonify({"message": "Pin added successfully"}), 201


@volunteer_bp.route("/api/get-pins", methods=["GET"])
def get_pins():
    pins = run_get_cmd("SELECT lat, lng FROM Pins")
    return jsonify([{"lat": pin[0], "lng": pin[1]} for pin in pins])


@volunteer_bp.route("/symbol", methods=["GET", "POST"])
def get_symbol():
    """_summary_

    Returns:
        _type_: _description_
    """
    # Retrieve the provided query parameters (if it exists)
    symbol_name = request.args.get("symbol_name", default=None, type=str)
    
    session = db.session
    
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


@volunteer_bp.get("/record_verifier")
def get_records():
    page = request.args.get("page", default=1, type=int)
    typ = request.args.get("type", default=-1, type=int)
    
    if page < 1:
        abort(400, f"Invalid page number: {page}")
    
    record_service = RecordService(typ)
    results = record_service.get_unverified_records(page)
    return jsonify(results), 200


@volunteer_bp.post("/record_verifier")
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
