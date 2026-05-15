"""
Application factory for the Flask backend.

Call 'create_app(config_name)' to instantiate and configure a Flask app with
the database, JWT, CORS, REST resources, and blueprints registered.
"""
import os

from flask import Flask
from flask_cors.extension import CORS
from flask_restful import Api
from werkzeug.middleware.proxy_fix import ProxyFix

from backend.extensions import jwt, bcrypt
from backend.src.api.api_core.decorators import register_jwt_access_token_refresh
from backend.src.api.api_core import exceptions
from .config.settings import config_selection
from .database import db

error_debugging: bool = True

def create_app(config_name=None):
    """Creates and configures a Flask application instance.

    Initializes extensions (e.g. SQLAlchemy, JWT...), registers routes, blueprints, and error handlers.

    Args:
        config_name (str | None): Config key used to select from 'config_selection'.
            If no config_name provided, default config is 'dev' (same as testing environment; to make it simpler, a test and prod config should suffice...)

    Returns:
        Flask: a fully configured Flask application instance.
    """
    
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True) # we're not using instance folders so maybe remove

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    if config_name is None:
        config_name = os.environ.get("FLASK_APP_ENV", "dev").lower() # retrieves specified environment, dev environment is default

    app.config.from_object(config_selection[config_name]())  # pop config; instantiate config class to access @property from said class as desired

    print("=" * 50)
    print(f"Environment: {config_name}")
    print(f"Debug Mode: {app.config['DEBUG']}")
    print(f"Testing: {app.config['TESTING']}")
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"Secret Key Set: {bool(app.config.get('SECRET_KEY'))}") #if exists, show boolean
    print(f"JWT Secret Key Set: {bool(app.config.get('JWT_SECRET_KEY'))}") 
    print("=" * 50)
    
    # Used to define whether exceptions should be shown to client
    global error_debugging
    error_debugging = app.config['DEBUG'] or app.config['TESTING']

    db.init_app(app) # load settings for db engine/ bind flask-alchemy to app; flask-alchemy currently used as a connection manager with our raw sql lol
    jwt.init_app(app)
    bcrypt.init_app(app)

    register_jwt_access_token_refresh(app)

    api = Api(app)

    CORS(app, supports_credentials=True, origins=[os.environ.get("FRONTEND_BASE_URL","http://localhost:3000")]) # added CSRF protection to enable supports_credentials=True via getCsrfToken() and X-CSRF-TOKEN headers added to frontend

    if app.config['TESTING']:
        api.resources = []  # Necessary to reset instances between tests
    
    # Import unique to specific app instance
    from .src.api.user_preferences_api import UserPreferences
    from .src.api.load_example_data import LoadExampleData
    from .src.api.notification_handler import NotificationService
    from .src.api.pushover_updater import PushoverUpdater
    from .src.api.record_collation import RecordCollation
    from .src.api.signal_update_handler import SignalUpdater
    from .src.api.station_auth import StationAuth
    from .src.api.station_online import StationOnline
    # from .src.api.symbol_api import SymbolAPI  # moved to volunteer handler since only volunteers need to interact with symbols
    from .src.api.time_frame_pull import recent_activities
    from .src.api.train_history import HistoryDB

    # register routes (some are useless)
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
    # api.add_resource(SymbolAPI, "/api/symbols")  # moved to volunteer handler since only volunteers need to interact with symbols
    api.add_resource(PushoverUpdater, "/api/PushoverUpdater")
    api.add_resource(RecordCollation, "/api/record_collation")
    api.add_resource(UserPreferences, '/api/user_preferences')
    api.add_resource(StationOnline, "/api/station_online")

    # blueprints + error handler registrations here
    from .src.api import user_api, station_handler, volunteer_handler

    app.register_blueprint(user_api.user_bp)
    app.register_blueprint(station_handler.station_bp)
    app.register_blueprint(volunteer_handler.volunteer_bp)

    exceptions.register_error_handlers(app) 

    return app