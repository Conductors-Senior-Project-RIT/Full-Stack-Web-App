# doc says config .py files should have all uppercase for config keys
# default settings would refer to dev environment
# TODO: def missing some variables to set, but will add along the way
import os

class Config(object):
    """
    Base configuration class
    """
    # default config setting(s)
    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-key?")

    # build database uri from .env | should prod config database url be stored in .env?
    @staticmethod
    def get_database_uri():
        host = os.environ.get("DB_HOST")
        database = os.environ.get("DB_NAME")
        user = os.environ.get("DB_USER")
        password = os.environ.get("DB_PASSWORD")
        port = os.environ.get("DB_PORT")

        db_uri = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"

        return db_uri

class ProdConfig(Config):
    """
    Production environment configuration - note sure if raising errors is necessary here but ill leave it for now
    """
    DEBUG = False

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URI")
    SECRET_KEY = os.environ.get("SECRET_KEY")

    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("Must provide DATABASE_URI environment variable for prod environment. Please set it.")

    if not SECRET_KEY:
        raise ValueError("Must provide SECRET_KEY environment variable for prod environment. Please set it.")

    # Prod specific settings
    SESSION_COOKIE_SECURE = True  # send cookies over HTTPS only
    SESSION_COOKIE_HTTPONLY = True

class DevConfig(Config):
    """
    Dev environment configuration
    """
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = Config.get_database_uri()

class TestConfig(Config):
    """
    Test environment configuration
    """
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = Config.get_database_uri()

config_selection = {"dev": DevConfig,
                 "prod": ProdConfig,
                 "test": TestConfig,
                 "default": DevConfig,}



