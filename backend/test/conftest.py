# start files and functions with test_

# Each test will create a new temporary database file and populate some data that will be used in the tests.

import unittest
import os
from flask import current_app

from backend import create_app

# with open(os.path.join(os.path.dirname(__file__), 'data.sql'), 'rb') as f:
#     _data_sql = f.read().decode('utf8')

# all tests classes will inherit this class to not duplicate testing setup
class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True,
                               "FLASK_APP_ENV": "test",
                               })  # maybe let .env.test still configure database and remove run_test.sh
        # flask test client simulating http requests
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push() # provides current_app
        # db.create_all() will this work or reflection needed somehow?

    def tearDown(self):
        # dont forget db and  session
        self.app = None
        self.ctx.pop()
        self.client = None

    def test_app(self):
        assert self.app is not None
        assert current_app == self.app