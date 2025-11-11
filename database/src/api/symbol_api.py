from flask import request, jsonify
from flask_restful import Resource, reqparse
from db.symbols_db import *


class SymbolAPI(Resource):

    def get(self):
        """Retrieves and returns a list of symbol names as strings if a "symbol_name" is not provided in the request arguments.
        If a symbol name is provided where the corresponding value is a string, the endpoint will return the ID of the provided 
        symbol from the database.

        Returns:
            Response: A response with a payload including either a list of symbol names or a symbol ID.
        """
        # Attempt to get the symbol name from the request args if present
        symbol_name = request.args.get("symbol_name", type=str, default=None)
        
        # If a symbol name is not provided, then attempt to return a list of symbol names in the databse.
        if not symbol_name:
            results = get_symbol_names()
            if not results:
                return jsonify({"error": "The server encountered an error when fetching symbol names!"}), 500
            return results, 200
        
        # Otherwise, attempt to return the ID that corresponds to a provided symbol name.
        else:
            symbol_id = get_symbol_id_by_name(symbol_name)
            if not symbol_id:
                return jsonify({"error": "The server encountered an error when fetching a symbol ID!"}), 500
            return jsonify({"id": symbol_id}), 200
        

    def post(self):
        """Inserts a new symbol into the database given a "symbol_name" provided in the request arguments.

        Returns:
            (Request): A payload including a status message and the response code.
        """
        #TODO: The endpoint should return a payload regardless of success or error. Not sure how the front-end handles the request.
        # Get the symbol name from the request parameters
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str, default=None)
        args = parser.parse_args()

        # If there is no name provided, then return a 400 error
        if not args["name"]:
            return jsonify({"error": "Must provide a symbol name for a new symbol!"}), 400
        
        # Otherwise, attempt to insert the new symbol and return the status
        return 200 if insert_new_symbol() else 500
