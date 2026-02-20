import os
from flask import Flask
from flask_cors.extension import CORS

from backend.extensions import bcrypt, jwt, api

from .src.api.UserPreferencesAPI import UserPreferences
from .src.api.load_example_data import LoadExampleData
from .src.api.notification_handler import NotificationService
from .src.api.pushover_updater import PushoverUpdater
from .src.api.record_collation import RecordCollation
from .src.api.signal_update_handler import SignalUpdater
from .src.api.station_auth import StationAuth
from .src.api.station_online import StationOnline
from .src.api.symbol_api import SymbolAPI
from .src.api.time_frame_pull import recent_activities
from .src.api.train_history import HistoryDB
from .config.settings import config_selection

from dotenv import load_dotenv

load_dotenv()  # .env file --> load_dotenv() --> .env vars go into os.environ --> settings.py reads that stuff -> that's it?
# okay then just add .env at root of project and see if stuff runs lol

def create_app():
    """
    TODO: config setup almost done? just need to add more customizations in settings.py + reflect tables and add more as i continue refactoring?
    idea: make script for dev/testing/prod envs, all it will do is export variables and do
    "flask run" for non prod stuff and prod will have its own special stuff
    """

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    "not sure if comments below are needed"
    # ensure the instance folder exists
    # os.makedirs(app.instance_path, exist_ok=True)
    # load default config
    # app.config.from_object('config.default_settings') # config/placeholder.py
    # create config file as such: instance/config.py and override any config settings you desire there.
    # app.config.from_pyfile('config.py', silent=True)

    # retrieves specified environment, dev environment is default
    env = os.environ.get("FLASK_APP_ENV", "dev").lower()
    app.config.from_object(config_selection[env]()) # pop config; instantiate config class to access @property from said class as desired

    from db import db
    db.init_app(app) # load settings for db engine/ bind sqlaclhemy to app (flask-alchemy)
    # TODO: reflect existing tables here with the "db" (it's a quick way to get models for existing db tables (?) -- look into more)

    # winging the setup here lol
    CORS(app)
    api.init_app(app)
    bcrypt.init_app(app) # find old commit to plug back old hashing algorithm
    jwt.init_app(app)

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
    api.add_resource(SymbolAPI, "/api/symbols")
    api.add_resource(PushoverUpdater, "/api/PushoverUpdater")
    api.add_resource(RecordCollation, "/api/record_collation")
    api.add_resource(UserPreferences, '/api/user_preferences')
    api.add_resource(StationOnline, "/api/station_online")

    # blueprints + error handler registrations here
    from src.api import user_api, station_handler, volunteer_handler, error_handler

    app.register_blueprint(user_api.user_bp)
    app.register_blueprint(station_handler.station_bp)
    app.register_blueprint(volunteer_handler.volunteer_bp)

    error_handler.register_error_handlers(app)  # - commenting out for now

    print("env: ",env) # double check env value
    print(f"debug value: {app.config["DEBUG"]}") # double check in right env

    return app




