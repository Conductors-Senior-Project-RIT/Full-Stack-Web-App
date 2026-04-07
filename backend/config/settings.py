# doc says config .py files should have all uppercase for config keys
# default settings would refer to dev environment
# TODO: def missing some variables to set, but will add along the way
import os

class Config(object):
    """
    Base configuration class
    """
    # default config setting(s)
    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")

class ProdConfig(Config):
    """
    Production environment configuration - note sure if raising errors is necessary here but ill leave it for now
    """
    # DEBUG = False by default
    TESTING = False
    SESSION_COOKIE_SECURE = True  # send cookies over HTTPS only
    SESSION_COOKIE_HTTPONLY = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("PROD_DATABASE_URI")

    # if not SQLALCHEMY_DATABASE_URI: causes error @ class definition time, can add these checkers in create_app()
    #     raise ValueError("Must provide DATABASE_URI environment variable for prod environment. Please set it.")

    # if not SECRET_KEY:
    #     raise ValueError("Must provide SECRET_KEY environment variable for prod environment. Please set it.")

class DevConfig(Config):
    """
    Dev environment configuration
    """
    # DEBUG = True | use --debug flag for the development environment (as per docs; script does this).
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DEV_DATABASE_URI", "postgresql+psycopg2://postgres:ReginaLatinae$24@localhost:5432/seniorprojecttest") # falls back to default testing db

class TestConfig(Config):
    """
    Test environment configuration
    """
    TESTING = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "test-secret")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "test-jwt")
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URI", "postgresql+psycopg2://test_user:pass@localhost:5432/test_db")

config_selection = {"dev": DevConfig,
                 "prod": ProdConfig,
                 "test": TestConfig,
                 "default": DevConfig,}



