from flask import Flask
from flask_cors import CORS
from flask_restful import Resource, Api
from api.train_history import *
from api.train_test import *
from api.reset_db import *
from api.user_api import *
from api.notification_handler import *
from api.signal_update_handler import *
from api.admin_handler import admin_bp  # Import the admin blueprint
from api.station_handler import station_bp
from api.load_example_data import (
    LoadExampleData,
)  # Import the load example data resource
from api.station_auth import StationAuth
from api.log_verifier import LogVerifier
from api.time_frame_pull import recent_activities
from api.symbol_api import SymbolAPI
from api.verifier_hot import LogVerifierHOT
from api.pushover_updater import PushoverUpdater
from api.data_collation import DataCollation
from api.UserPreferencesAPI import UserPreferences
from api.station_online import StationOnline
from api.hot_collation import HotCollation

app = Flask(__name__)
api = Api(app)

# Replace with your actual PostgreSQL credentials
app.config["SECRET_KEY"] = "your_secret_key"
app.config["JWT_SECRET_KEY"] = "your_jwt_secret_key"

CORS(app)
bcrypt.init_app(app)
jwt.init_app(app)

api.add_resource(HistoryDB, "/api/history")
# api.add_resource(Train_Test, "/api/test_setup")
# api.add_resource(ResetDB, "/api/reset")
api.add_resource(NotificationService, "/api/notify")
api.add_resource(
    LoadExampleData, "/api/load-example-data"
)  # Register the load example data resource
api.add_resource(SignalUpdater, "/api/add_signal_info")
api.add_resource(StationAuth, "/api/station_auth")
api.add_resource(LogVerifier, "/api/verifier")
api.add_resource(recent_activities, "/api/recent_activities")
api.add_resource(SymbolAPI, "/api/symbols")
api.add_resource(LogVerifierHOT, "/api/verifier_hot")
api.add_resource(PushoverUpdater,"/api/PushoverUpdater")
api.add_resource(DataCollation, "/api/data_collation")
api.add_resource(UserPreferences, '/api/user_preferences')
api.add_resource(StationOnline, "/api/station_online")
api.add_resource(HotCollation, '/api/hot_collation')

app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(station_bp)

if __name__ == "__main__":
    app.run(debug=True)
