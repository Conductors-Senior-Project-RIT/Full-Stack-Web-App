from flask import Flask
from flask_restful import Api
from api.train_history import *
from api.user_api import *
from api.notification_handler import *
from api.signal_update_handler import *
from backend.src.api.volunteer_handler import volunteer_bp  # Import the admin blueprint
from api.station_handler import station_bp
from api.load_example_data import (
    LoadExampleData,
)  # Import the load example data resource
from api.station_auth import StationAuth
from api.error_handler import register_error_handlers
from api.time_frame_pull import recent_activities
from api.symbol_api import SymbolAPI
from api.pushover_updater import PushoverUpdater
from api.record_collation import RecordCollation
from api.UserPreferencesAPI import UserPreferences
from api.station_online import StationOnline
from backend.db import db, db_uri


app = Flask(__name__)
api = Api(app)

# Replace with your actual PostgreSQL credentials
app.config["SECRET_KEY"] = "your_secret_key"
app.config["JWT_SECRET_KEY"] = "your_jwt_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = db_uri

# Initialize our Flask app with our PostgreSQL
db.init_app(app)

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
api.add_resource(recent_activities, "/api/recent_activities")
api.add_resource(SymbolAPI, "/api/symbols")
api.add_resource(PushoverUpdater,"/api/PushoverUpdater")
api.add_resource(RecordCollation, "/api/record_collation")
api.add_resource(UserPreferences, '/api/user_preferences')
api.add_resource(StationOnline, "/api/station_online")

app.register_blueprint(user_bp)
app.register_blueprint(volunteer_bp)
app.register_blueprint(station_bp)

register_error_handlers(app)

if __name__ == "__main__":
    app.run(debug=True)
