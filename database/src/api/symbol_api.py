from flask import jsonify
from flask_restful import Resource, reqparse
from src.db.trackSense_db_commands import *


class SymbolAPI(Resource):

    def get(self):
        # returns all symbol names in a list
        sql = """
            SELECT symb_name FROM Symbols
        """

        resp = run_get_cmd(sql)
        ret_val = [
            tup[0] for tup in resp
        ]  # run_get_cmd() returns a list of tuples, doing this gives us an array of symbols.
        print(ret_val)  # testing print
        return ret_val

    def post(self):
        # insert a new symbol into the db

        # prepared statement
        sql = """
            INSERT INTO Symbols (symb_name) VALUES
            (%(name)s)
        """
        # get the symbol name
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str, default="unknown")
        args = parser.parse_args()

        # execute the sql statement
        run_exec_cmd(sql, args={"name": args["name"]})
        return 200
