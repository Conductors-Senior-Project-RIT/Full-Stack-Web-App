import unittest
from unittest.mock import Mock
from src.api import station_auth

class TestStationAuth(unittest.TestCase):
    def setUp(self):
        station_auth.random = Mock()
        self.station_auth = station_auth.StationAuth()

    def test_generate_password_string(self):
        station_auth.random.randint = Mock(return_value=12)
        station_auth.random.choice = Mock(return_value="A")
        (pw, hash_pw) = self.station_auth.generate_password_string()
        self.assertEqual("AAAAAAAAAAAA", pw, msg="Password incorrect.")
        self.assertEqual("0592cedeabbf836d8d1c7456417c7653ac208f71e904d3d0ab37faf711021aff", hash_pw, msg="Hash incorrect.")