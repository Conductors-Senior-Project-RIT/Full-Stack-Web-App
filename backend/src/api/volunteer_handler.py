from flask import Blueprint, abort, request
from flask_restful import reqparse
from werkzeug.exceptions import BadRequest

from backend.src.global_core.decorators import role_required
from ..service.record_service import RecordService
from ..service.symbol_service import SymbolService
# from ..db.trackSense_db_commands import *
from backend.database import db

volunteer_bp = Blueprint("volunteer_bp", __name__)

"""
NOTE: Pins table doesn't have "lat" or "lng" fields so an error will always occur... hence me commenting out those routes for now at least.
"""

# @volunteer_bp.route("/api/add-pin", methods=["POST"])
# @role_required(0, 1)
# def add_pin():
#     data = request.get_json()
#     lat = data.get("lat")
#     lng = data.get("lng")

#     if lat is None or lng is None:
#         return {"message": "Invalid data"}, 400

#     # Insert the pin into the database
#     run_exec_cmd("INSERT INTO Pins (lat, lng) VALUES (%s, %s)", (lat, lng))
#     return {"message": "Pin added successfully"}, 201


# @volunteer_bp.route("/api/get-pins", methods=["GET"])
# @role_required(0, 1)
# def get_pins():
#     pins = run_get_cmd("SELECT lat, lng FROM Pins")
#     return [{"lat": pin[0], "lng": pin[1]} for pin in pins]


@volunteer_bp.route("/api/symbol", methods=["GET", "POST"])
@role_required(0, 1)
def get_symbol():
    """_summary_

    Returns:
        _type_: _description_
    """

    # Retrieve the provided query parameters (if it exists)
    symbol_name = request.args.get("symbol_name", default=None, type=str)
    
    session = db.session
    
    # Instantiate a symbol service
    service = SymbolService(session)

    if request.method == "GET":
        # The service supports an undefined symbol name and always returns a list
        results = service.get_symbol(symbol_name)
        
        # Return results in the 'results' field for consistency
        return {"results": results}, 200
    
    elif request.method == "POST":
        # To create a new symbol, a name must be provided
        if symbol_name is None:
            abort(400, "Must provide a symbol name to create a record!")

        # If a name is provided, then use the service to create a new symbol
        service.create_symbol(symbol_name)
        session.commit()
    return {}, 200


@volunteer_bp.get("/api/record_verifier")
@role_required(0, 1)
def get_records():
    page = request.args.get("page", default=1, type=int)
    typ = request.args.get("type", default=-1, type=int)
    
    if page < 1:
        abort(400, f"Invalid page number: {page}")
    
    session = db.session

    record_service = RecordService(session, typ)
    results = record_service.get_unverified_records(page)
    return results, 200


@volunteer_bp.post("/api/record_verifier")
@role_required(0, 1)
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
            raise BadRequest(f"{arg} must be greater than 1, given: {val}")
    
    session = db.session
    record_service = RecordService(session, args.type)
    record_service.verify_record(args.id, args.symbol, args.engine_number)
    return {}, 200
