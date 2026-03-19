import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from sqlalchemy import Result
from sqlalchemy.orm.scoping import scoped_session

from backend.database import db
from backend.src.db.database_core import RepositoryInternalError, RepositoryInvalidArgumentError, RepositoryNotFoundError
from backend.src.db.hot_repo import HOTRepository
from backend.test.base_test_case import BaseTestCase

class TestHOTRecordRepository(BaseTestCase):
    def setUp(self):
        super().setUpClass()
        self.session = db.session
        self.repo = HOTRepository(self.session)
        
    def tearDown(self):
        self.session.rollback() # revert changes made from every test_method ran
        self.session.close()


    ###############
    ##  Getters  ##
    ###############
    def testGetters(self):
        self.assertEqual("HOT Record", self.repo.get_record_name())
        self.assertEqual("hot", self.repo.get_record_identifier())
        
    
    ##########################
    ##  get_train_record()  ##
    ##########################
    def testGetTrainRecord(self):
        # Only need to test successful path for child classes
        expected = {
            "id": 0,
            "date_rec": datetime.strptime('1999-01-08 04:10:21', "%Y-%m-%d %H:%M:%S"),
            "station_recorded": 0,
            "symbol_id": None,
            "engine_num": None,
            "frame_sync": "UNKNOWN",
            "unit_addr": "1234",
            "command": "UNKNOWN",
            "checkbits": "UNKNOWN",
            "parity": "UNKNOWN",
            "verified": False,
            "verifier_id": None,
            "most_recent": False,
            "locomotive_num": "unknown",
            "signal_strength": 0.0
        }
        
        result = self.repo.get_train_record(0)
        self.assertDictEqual(expected, result)
    

    ###########################
    ##  get_train_history()  ##
    ###########################
    def testGetTrainHistorySuccess(self):
        expected = [{
            "id": 1,
            "date_rec": datetime.strptime('2001-02-04 01:23:45', "%Y-%m-%d %H:%M:%S"),
            "station_name": "test station",
            "symbol_id": None,
            "unit_addr": "5678",
            "command": "UNKNOWN",
            "checkbits": "UNKNOWN",
            "parity": 'UNKNOWN',
            "verified": False
        }]
        
        results = self.repo.get_train_history(1, 1, 250)
        self.assertListEqual(expected, results)
        
    def testGetTrainHistoryBadID(self):
        expected = []
        results = self.repo.get_train_history(-1, 1, 250)
        self.assertListEqual(expected, results)
        
    
    #############################
    ##  create_train_record()  ##
    #############################
    def testCreateTrainRecordDatetimeSuccess(self):
        date = datetime.strptime('2025-02-04 09:23:45', "%Y-%m-%d %H:%M:%S")
        # Test with datetime string in args dict
        args = {
            "date_rec": date,
            "station_id": 1,
            "frame_sync": "test",
            "command": "test",
            "checkbits": "test",
            "parity": "test",
            "unit_addr": "test"
        }
        
        expected = {
            "id": 3,
            "date_rec": date,
            "station_recorded": 1,
            "symbol_id": None,
            "engine_num": None,
            "frame_sync": "test",
            "unit_addr": "test",
            "command": "test",
            "checkbits": "test",
            "parity": "test",
            "verified": False,
            "verifier_id": None,
            "most_recent": True,
            "locomotive_num": "unknown",
            "signal_strength": 0.0
        }
        
        result, recov = self.repo.create_train_record(args, None)
        self.assertEqual(result, 3)
        self.assertEqual(recov, True)
        
        resulting_record = self.repo.get_train_record(3)
        self.assertDictEqual(expected, resulting_record)
        
        # Now test with datetime arg
        args["date_rec"] = None
        expected["id"] = 4
        
        result, recov = self.repo.create_train_record(args, date)
        self.assertEqual(result, 4)
        self.assertEqual(recov, False)
        
        resulting_record = self.repo.get_train_record(4)
        self.assertDictEqual(expected, resulting_record)
    
    def testCreateTrainRecordNoDatetime(self):
        args = {
            "date_rec": None,
            "station_id": 1,
            "frame_sync": "test",
            "command": "test",
            "checkbits": "test",
            "parity": "test",
            "unit_addr": "test"
        }
        
        with self.assertRaises(RepositoryInvalidArgumentError):
            self.repo.create_train_record(args, None)
            
    def testCreateTrainRecordDBFail(self):
        args = {
            "date_rec": datetime.strptime('2025-02-04 09:23:45', "%Y-%m-%d %H:%M:%S"),
            "station_id": 1,
            "frame_sync": "test",
            "command": "test",
            "checkbits": "test",
            "parity": "test",
            "unit_addr": "test"
        }
        
        with patch.object(Result, "scalar_one_or_none", return_value=None) as mock:
            with self.assertRaises(RepositoryInternalError):
                self.repo.create_train_record(args, None)
            
            mock.assert_called_once()
            
    
    ####################################
    ##  get_recent_station_records()  ##
    ####################################
    def testGetRecentStationRecords(self):
        self.maxDiff = None
        expected = [
            {
                "id": 1,
                "date_rec": datetime.strptime('2001-02-04 01:23:45', "%Y-%m-%d %H:%M:%S"),
                "station_recorded": 0,
                "symbol_id": None,
                "engine_num": None,
                "frame_sync": "UNKNOWN",
                "unit_addr": '5678',
                "command": "UNKNOWN",
                "checkbits": "UNKNOWN",
                "parity": "UNKNOWN",
                "verified": False,
                "verifier_id": None,
                "most_recent": True,
                "locomotive_num": "unknown",
                "signal_strength": 0.0
            },
            {
                "id": 2,
                "date_rec": datetime.strptime('2021-08-16 20:14:11', "%Y-%m-%d %H:%M:%S"),
                "station_recorded": 0,
                "symbol_id": None,
                "engine_num": None,
                "frame_sync": "UNKNOWN",
                "unit_addr": '9910',
                "command": "UNKNOWN",
                "checkbits": "UNKNOWN",
                "parity": "UNKNOWN",
                "verified": False,
                "verifier_id": None,
                "most_recent": True,
                "locomotive_num": "unknown",
                "signal_strength": 0.0
            }
        ]
        
        results = self.repo.get_recent_station_records(0)
        self.assertListEqual(expected, results)
        
    
    ###############################
    ##  parse_station_records()  ##
    ###############################
    def testParseStationRecords(self):
        # Test empty records
        self.assertListEqual([], self.repo.parse_station_records([]))
        self.assertListEqual([], self.repo.parse_station_records(None))
        
        # Test parsing of records
        expected = [
            {
                "id": 1,
                "date_rec": datetime.strptime('2001-02-04 01:23:45', "%Y-%m-%d %H:%M:%S"),
                "frame_sync": "UNKNOWN",
                "unit_addr": '5678',
                "command": "UNKNOWN",
                "checkbits": "UNKNOWN",
                "parity": "UNKNOWN"
            },
            {
                "id": 2,
                "date_rec": datetime.strptime('2021-08-16 20:14:11', "%Y-%m-%d %H:%M:%S"),
                "frame_sync": "UNKNOWN",
                "unit_addr": '9910',
                "command": "UNKNOWN",
                "checkbits": "UNKNOWN",
                "parity": "UNKNOWN"
            }
        ]
        
        records = self.repo.get_recent_station_records(0)
        results = self.repo.parse_station_records(records)
        self.assertListEqual(expected, results)
        
        
    
if __name__ == '__main__':
    unittest.main()