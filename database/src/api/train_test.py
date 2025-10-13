from flask_restful import Resource
from db.trackSense_db_commands import *

class Train_Test(Resource):
    def get(self):
        run_sql_file('..\\..\\config\\test_data.sql')
        print('setup done!')
        return 200