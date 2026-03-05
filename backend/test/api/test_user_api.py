import unittest
from backend.db import db
from backend.test.base_test_case import BaseTestCase

class TestUserApi(BaseTestCase):
    """
    todo: maybe have status_code map to an english word to avoid magic numbers
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass() #making sure parent method impl. runs
        cls.client = cls.app.test_client()  # creates class attribute to be referenced

    def test_register_user(self, email="test_email", password="test_password"):
        response = self.client.post(
            '/api/register',
            json={'email': email,'password': password}
        )

        expected_status_code = 201
        self.assertEqual(response.status_code, expected_status_code)
