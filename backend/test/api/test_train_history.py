import unittest
from unittest.mock import Mock
from werkzeug.exceptions import BadRequest

from backend.src.api.train_history import validate_int_argument

class TestTrainHistory(unittest.TestCase):
    def setUp(self):
        # HistoryDB.RecordService = Mock()
        # HistoryDB.db = Mock()
        # self.th = HistoryDB()
        pass
        
    def test_validate_int_value_not_int(self):
        name = "Test"
        value = "not an integer"
        min_value = 0
        with self.assertRaises(BadRequest) as cm:
            validate_int_argument(value, name, min_value)
        self.assertEqual(cm.exception.description, f"{name} ({value}) is not an integer!")
    
    def test_validate_int_min_not_int(self):
        name = "Test"
        value = 0
        min_value = "not an integer"
        with self.assertRaises(BadRequest) as cm:
            validate_int_argument(value, name, min_value)
        self.assertEqual(cm.exception.description, f"{name} minimum value {min_value} is not an integer.")
    
    def test_validate_int_less_than_min(self):
        name = "Test"
        value = 0
        min_value = 1
        with self.assertRaises(BadRequest) as cm:
            validate_int_argument(value, name, min_value)
        self.assertEqual(cm.exception.description, f"Provided {name} must be greater than {min_value} but was given {value}...")
        