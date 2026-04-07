import os
import unittest
from sqlalchemy import text

from backend import create_app
from ..database import db

"""
Initial setups for api and database test classes
./run_test.sh (look at run_test.sh briefly; if you wish to provide extra configuration values, edit .env.test)
"""

BASE_DIRECTORY = os.path.dirname(os.path.abspath(__file__)) # avoids FileNotFoundError from relative paths

class BaseTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Creates app context for flask to understand what app we're pointing to for a test class.
        Database uses "scoped_session" from flask-alchemy (thin wrapper of sqlalchemy) and it happens to be bound to a flask app.
        Creates variables that will be used in child test classes.
        """
        cls.app = create_app(config_name="test")
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        # TODO: create schema + mock data via ORM, not raw SQL so schema changes are automatically handled with Flask-Migrate
        cls.database_loader("table.sql")
        cls.database_loader("test_data.sql")

    @classmethod
    def database_loader(cls, file_name):
        """
        Helper method to load a mock database for testing purposes
        """
        file_location = os.path.join(BASE_DIRECTORY, file_name)
        with open(file_location, "r") as f:
            sql_text = f.read()

        with db.engine.connect() as conn:
            conn.execute(text(sql_text))
            conn.commit()

    @classmethod
    def tearDownClass(cls):
        db.session.remove() # releases connection and transaction resources so a new scoped_session can use it then closes session and discards the session itself.
        cls.app_context.pop()