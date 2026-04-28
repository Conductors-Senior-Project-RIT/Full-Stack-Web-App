import os
class Config(object):
    """
    Base configuration class
    """
    # default config setting(s)
    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = False

class ProdConfig(Config):
    """
    Production environment config
    """
    TESTING = False
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = True # HTTPS only
    JWT_COOKIE_CSRF_PROTECT = True # enabling CSRF in prod
    JWT_COOKIE_SAMESITE = "Lax"   
    SQLALCHEMY_DATABASE_URI = os.environ.get("PROD_DATABASE_URI")

class DevConfig(Config):
    """
    Dev environment config
    """
    JWT_COOKIE_SAMESITE = "Lax"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DEV_DATABASE_URI", "postgresql+psycopg2://test_user:pass@localhost:5432/test_db") # falls back to default testing db
    SECRET_KEY = os.environ.get("SECRET_KEY", "test-secret")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "test-jwt")

class TestConfig(Config):
    """
    Test environment config
    """
    TESTING = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "test-secret")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "test-jwt")
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URI", "postgresql+psycopg2://test_user:pass@localhost:5432/test_db")

config_selection = {"dev": DevConfig,
                 "prod": ProdConfig,
                 "test": TestConfig,
                 "default": DevConfig,}



