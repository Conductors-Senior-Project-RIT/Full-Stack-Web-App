from flask import Flask
from flask_cors import CORS
from flask_restful import Resource, Api
from api.train_history import *
from api.train_test import *
from api.reset_db import *

app = Flask(__name__)
api = Api(app)
CORS(app)

api.add_resource(HistoryDB, '/history')
api.add_resource(Train_Test, '/test_setup')
api.add_resource(ResetDB, '/reset')

if __name__ == '__main__':
    # run_sql_file('..\\..\\config\\table.sql')
    app.run()