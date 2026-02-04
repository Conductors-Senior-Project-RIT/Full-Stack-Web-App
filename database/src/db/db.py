from abc import ABC
import os
from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine
from sqlalchemy.orm.scoping import scoped_session
import yaml

        
db = SQLAlchemy()
db_uri = ""

full_config_path = os.path.join(os.path.dirname(__file__), '../../config/postgres_config.yml')
with open(full_config_path, 'r') as file:
    cfg = yaml.load(file, Loader=yaml.FullLoader)
    db_uri = f"postgresql+psycopg2://{cfg["user"]}:{cfg["password"]}@{cfg["host"]}:{cfg["port"]}/{cfg["database"]}"
