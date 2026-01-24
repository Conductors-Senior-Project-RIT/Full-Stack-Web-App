# THIS SHOULD ONLY BE USED FOR TESTING!!!
from flask_restful import Resource
from db.trackSense_db_commands import *


class ResetDB(Resource):
    def get(self):
        run_sql_file("../../config/table.sql")
        return 200
    