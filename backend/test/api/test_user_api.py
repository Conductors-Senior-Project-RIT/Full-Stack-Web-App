import unittest
from backend.db import db
from backend.test.base_test_case import BaseTestCase


class TestUserApi(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass() #making sure parent method impl. runs
        cls.client = cls.app.test_client()

    def test