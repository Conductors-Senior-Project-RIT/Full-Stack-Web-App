import os
import yaml
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)  # the db object gives you access to the db.Model class to define models, and the db.session to execute queries.

# def init_app(app):
    #
    # full_config_path = os.path.join(os.path.dirname(__file__), '../../config/postgres_config.yml') #may need to update path
    # with open(full_config_path, 'r') as file:
    #     cfg = yaml.load(file, Loader=yaml.FullLoader)
    #     db_uri = f"postgresql+psycopg2://{cfg["user"]}:{cfg["password"]}@{cfg["host"]}:{cfg["port"]}/{cfg["database"]}"

    # configure the SQLite database, relative to the app instance folder
    # app.config["SQLALCHEMY_DATABASE_URI"] = db_uri


    # initialize the app with the extension
    # db.init_app(app) # this function does all the heavy lifting for handling connections, and scoped_sessions

    # reflect existing tables here idk how to do it yet (we have existing db data so this is a quick way to get the models(?))

