# doc says config .py files should have all uppercase for config keys
# default settings would refer to dev environment
# TODO: def missing some variables to set, but will add along the way
import os

class Config(object):
    """
    Base configuration class
    """
    # default config setting(s)
    SECRET_KEY = os.environ.get("SECRET_KEY", "secret-key-def")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-secret-key-def")

class ProdConfig(Config):
    """
    Production environment configuration - note sure if raising errors is necessary here but ill leave it for now
    """
    # DEBUG = False by default
    TESTING = False
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_COOKIE_SECURE = True
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://tracksense:skillissue@localhost:5432/tracksense"

class DevConfig(Config):
    """
    Dev environment configuration
    """
    # DEBUG = True | use --debug flag for the development environment (as per docs; script does this).
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DEV_DATABASE_URI", "postgresql+psycopg2://test_user:pass@localhost:5432/test_db") # falls back to default testing db

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



