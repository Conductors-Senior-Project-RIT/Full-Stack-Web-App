import unittest
from unittest.mock import Mock
from src.api import station_auth
from src.db import trackSense_db_commands
import random

class TestStationAuth(unittest.TestCase):
    def setUp(self):
        station_auth.random = Mock()
        
        self.station_auth = station_auth.StationAuth

    def test_generate_password_string(self):
        random.randint = Mock(return_value=12)
        self.station_auth.generate_password_string()