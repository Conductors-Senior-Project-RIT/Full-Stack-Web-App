import unittest
from unittest.mock import Mock, patch
from werkzeug.exceptions import BadRequest
from datetime import datetime

from backend import create_app
from backend.src.api.train_history import validate_int_argument, HistoryDB

class TestTrainHistory(unittest.TestCase):
    @patch('backend.init_models')
    def setUp(self, mock_models):
        app = create_app(config_name="test")
        app.testing = True
        self.client = app.test_client()
        
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
    
    @patch("backend.src.api.train_history.db")
    def test_get_hot_success(self, mock_db):
        mock_db.session = Mock()
        hot_rec = [{
            "id": 1,
            "date_rec": str(datetime.strptime('2001-02-04 01:23:45', "%Y-%m-%d %H:%M:%S")),
            "station_name": "test station",
            "symbol_id": None,
            "unit_addr": "5678",
            "command": "UNKNOWN",
            "checkbits": "UNKNOWN",
            "parity": 'UNKNOWN',
            "verified": False
        }]
        with patch("backend.src.api.train_history.RecordService") as mock_rs:
            instance = mock_rs.return_value
            instance.get_train_history.return_value = hot_rec
            response = self.client.get("/api/history", query_string={"type": 2, "id": 1})
            self.assertEqual(response.status_code, 200)
            instance.get_train_history.assert_called_with(1, 1)
            self.assertEqual(response.json, hot_rec)
    
    @patch("backend.src.api.train_history.db")
    def test_post_eot_success(self, mock_db):
        mock_db.session = Mock()
        eot_data = {
            "type": 1,
            "station_id": 1,
            "unit_addr": "1234",
            "brake_pressure": "UNKNOWN",
            "motion": "UNKNOWN",
            "marker_light": "UNKNOWN",
            "turbine": "UNKNOWN",
            "battery_cond": "UNKNOWN",
            "battery_charge": "UNKNOWN",
            "arm_status": "UNKNOWN",
            "signal_strength": 1,
        }
        with patch("backend.src.api.train_history.RecordService") as mock_rs:
            instance = mock_rs.return_value
            instance.post_train_history.return_value = None
            response = self.client.post("/api/history", json=eot_data)
            self.assertEqual(response.status_code, 201)
        

        
