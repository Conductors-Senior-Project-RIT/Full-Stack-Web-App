"""Volunteer and admin endpoints for symbol management and record verification.

Routes here are restricted to admin (role 0) and volunteer (role 1) users only.
"""
from flask import Blueprint, request
from flask_restful import reqparse
from werkzeug.exceptions import BadRequest

from backend.database import db
from backend.src.api.api_core.decorators import role_required
from ..service.record_service import RecordService
from ..service.symbol_service import SymbolService

volunteer_bp = Blueprint("volunteer_bp", __name__)


# The following endpoints were originally intended to manage map pins, but the feature was unused when we received the project. 
# The code is left here for reference, but the endpoints are currently disabled.
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


@volunteer_bp.get("/api/symbols")
@role_required(0, 1)
def get_symbol():
    """Retrieves a symbol ID by name, or a list of all symbol names if no name is provided.

    Arguments should be provided as query parameters in the request URL.

    Args:
        symbol_name (str, optional): The name of a symbol. If provided, returns its
            corresponding ID; otherwise, a list of all symbol names is returned.

    Returns:
        Response: A JSON object containing either the ID of the symbol with the provided
            name under the key `results` or a list of all symbol names under the same
            key.
    """
    symbol_name = request.args.get("symbol_name", default=None, type=str)

    # Retrieve the provided query parameters (if it exists)
    session = db.session
    
    # Instantiate a symbol service, this method supports an undefined symbol name
    service = SymbolService(session)
    results = service.get_symbol(symbol_name)
    
    # Return results in the 'results' field for consistency
    return {"results": results}, 200
    
    
@volunteer_bp.post("/api/symbols")
@role_required(0, 1)
def post_symbol():
    """Creates a new symbol with the provided symbol name.

    Argument should be provided in the request body as a JSON object.

    Args:
        name (str): The name of the symbol to create.

    Returns:
        Response: The newly created symbol's ID under the key `id`.

    Raises:
        `BadRequest`: If no symbol name is provided in the request body.
    """
    # Get the symbol name if it exists
    data = request.get_json()
    symbol_name = data.get("name") if data else None
    
    # To create a new symbol, a name must be provided
    if symbol_name is None:
        raise BadRequest("Must provide a symbol name to create a record!")

    # Retrieve the provided query parameters (if it exists)
    session = db.session
    
    # Instantiate a symbol service
    service = SymbolService(session)

    # If a name is provided, then use the service to create a new symbol
    symb_id = service.create_symbol(symbol_name)
    session.commit()
    
    return {"id": symb_id}, 200


@volunteer_bp.get("/api/record_verifier")
@role_required(0, 1)
def get_records():
    """Retrieves a paginated list of unverified records for a given record type.

    Arguments should be provided as query parameters in the request URL.

    Args:
        page (int, optional): The page corresponding to a collection of records to
            return. Default: 1
        type (int): The type of train records to return. EOT: 1, HOT: 2, DPU: 3.
            Currently, DPU is not supported.

    Returns:
        Response: Returns a paginated collation of unverified records.

    Raises:
        `BadRequest`: If the provided page number is less than 1
    """
    page = request.args.get("page", default=1, type=int)
    typ = request.args.get("type", default=-1, type=int)
    
    if page < 1:
        raise BadRequest(f"Invalid page number: {page}")
    
    # Create a request-specific database session
    session = db.session

    # Call the record service to retrieve the unverified records, and return the results
    record_service = RecordService(session, typ)
    results = record_service.get_unverified_records(page)
    return results, 200


@volunteer_bp.post("/api/record_verifier")
@role_required(0, 1)
def post_record():
    """Verifies a train record by assigning a symbol and engine number. *Should be a PUT
    request, but last year's team used POST.*

    Arguments should be provided in the request body as a JSON object.

    Args:
        id (int): The ID of the record to verify. Must be greater than 0.
        type (int): The type of the record to verify. EOT: 1, HOT: 2, DPU: 3. Currently,
            DPU is not supported.
        symbol (int): The ID of the symbol being assigned to a record. This column is
            not updated if a value is not provided, or the value is less than `1`.
        locomotive (str, optional): The locomotive number being assigned to a record.
            This column is not updated if a value is not provided.

    Returns:
        Response: Returns an empty response with a 200 status code.

    Raises:
        `BadRequest`: If the record ID or symbol ID is less than 1.
    """
    parser = reqparse.RequestParser()
    parser.add_argument("id", type=int, default=-1)
    parser.add_argument("type", type=int, default=-1)
    parser.add_argument("symbol", type=int, default=-1)
    parser.add_argument("locomotive", type=str, default=None)
    args = parser.parse_args()
    
    if args.id < 1:
        raise BadRequest(f"Record ID must be greater than 1, given: {args.id}")
    
    if args.symbol < 1:
        raise BadRequest(f"Symbol ID must be greater than 1, given: {args.symbol}")
    
    # Create a request-specific database session
    session = db.session
    
    # Call the record service to verify the record, and commit the changes to the database
    record_service = RecordService(session, args.type)
    record_service.verify_record(args.id, args.symbol, args.locomotive)
    session.commit()
    return {}, 200
