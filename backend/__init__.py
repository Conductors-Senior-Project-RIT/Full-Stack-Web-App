import os
from flask import Flask
from .config.settings import config_selection
"""
1) ditch yaml (handled with settings.py and .env)
1.1) will setup .env .example and docs for specifying which env you which to use
WIP
"""

def create_app():
    """
    TODO: finish config setup --> lowkenuinely is this almost done? just need to add more customizations in settings.py?
    idea: make script for dev/testing/prod envs, all it will do is export variables and do
    "flask run" for non prod stuff and prod will have its own special stuff
    """

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # load default config
    # app.config.from_object('config.default_settings') # config/file.py

    # create config file as such: instance/config.py and override any config settings you desire there.
    # app.config.from_pyfile('config.py', silent=True)

    # retrieves specified environment, dev environment is default
    env = os.environ.get("FLASK_APP_ENV", "dev").lower()
    app.config.from_object(f"config.{config_selection[env]}") # pop config class; creates "config.DevConfig" string etc

    from .db import init_app
    init_app(app) # load settings for db engine/ bind sqlaclhemy to app

    # blueprints + error handler registrations here

    from src.api import user_api, station_handler, volunteer_handler#, error_handler

    app.register_blueprint(user_api.user_bp)
    app.register_blueprint(station_handler.station_bp)
    app.register_blueprint(volunteer_handler.volunteer_bp)

    #error_handler.register_error_handlers(app) - commenting out for now

    return app




