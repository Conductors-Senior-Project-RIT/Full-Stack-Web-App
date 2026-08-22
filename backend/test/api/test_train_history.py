import unittest
from unittest.mock import Mock, patch
from werkzeug.exceptions import BadRequest
from datetime import datetime

from backend import create_app
from backend.src.api.train_history import HistoryDB

class TestTrainHistory(unittest.TestCase):
    def setUp(self):
        app = create_app(config_name="test")
        app.testing = True
        self.client = app.test_client()
    
    
    def test_argument_check(self):
        response = self.client.get("/api/history", query_string={"type": 1, "id": 0})
        self.assertEqual(response.status_code, 400)
        
    
    @patch("backend.src.api.train_history.db")
    def test_get_hot_success(self, mock_db):
        mock_db.session = Mock()
        hot_rec = [{
            "id": 1,
            "date_rec": str(datetime.strptime('1999-01-08 04:05:06', "%Y-%m-%d %H:%M:%S")),
            "station_name": "test station1",
            "symb_name": "Test Symbol1",
            "unit_addr": "727",
            "frame_sync": "unknown",
            "command": "unknown",
            "checkbits": "unknown",
            "parity": 'unknown',
            "verified": False
        }]
        with patch("backend.src.api.train_history.RecordService") as mock_rs:
            instance = mock_rs.return_value
            instance.get_train_record.return_value = hot_rec
            response = self.client.get("/api/history", query_string={"type": 2, "id": 1})
            self.assertEqual(response.status_code, 200)
            instance.get_train_record.assert_called_with(1)
            self.assertEqual(response.json, hot_rec)
    
    @patch("backend.src.api.train_history.db")
    def test_post_eot_success(self, mock_db):
        mock_db.session = Mock()
        eot_data = {
            "type": 1,
            "date_rec": '1999-01-08 04:05:06',
            "station_id": 1,
            "symbol_id": 1,
            "unit_addr": "727"
        }
        with patch("backend.src.api.train_history.RecordService") as mock_rs:
            instance = mock_rs.return_value
            instance.create_train_record.return_value = None
            response = self.client.post("/api/history", json=eot_data)
            self.assertEqual(response.status_code, 201)
        

        
