from flask import jsonify
from flask_restful import Resource, reqparse, request
from db.trackSense_db_commands import *


class SymbolRegister(Resource):

    def get(self):

        # get symbol name from api request
        # parser = reqparse.RequestParser()
        # parser.add_argument("symbol_name", type=str, default="")
        # # get the symbol name from the arguments
        # args = parser.parse_args()
        symb_name = request.args.get("symbol_name")

        print(symb_name)
        # returns all symbol names in a list
        sql = """
            SELECT id FROM Symbols
            WHERE symb_name = %(name)s
        """

        resp = run_get_cmd(sql, args={"name": symb_name})[0][0]

        processed_data = jsonify({"id": resp})  # testing print
        return processed_data
