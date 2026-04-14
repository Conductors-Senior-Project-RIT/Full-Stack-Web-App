from pprint import pprint
import unittest
import math
from types import TracebackType
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import Session

from record_tests import collation_valid, compare_results
from backend.src.db.db_core.exceptions import RepositoryInternalError, RepositoryInvalidArgumentError, RepositoryNotFoundError, RepositoryParsingError
from backend.database import db
from backend.src.db.hot_repo import HOTRepository
from backend.test.base_test_case import BaseTestCase

class TestHOTRecordRepository(BaseTestCase):
    def setUp(self):
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
        
    
    #########################
    ##  get_train_history  ##
    #########################
    def testGetTrainHistory(self):
        expected_record = self.repo.get(1)
        expected_record["station_name"] = "test station1"
        expected_record["date_rec"] = str(expected_record["date_rec"])
        
        results = self.repo.get_train_history(1, 1, 250)
        valid, msg = compare_results(results, [expected_record])
        self.assertTrue(valid, msg)
        
        results = self.repo.get_train_history(17, 1, 250)
        self.assertEqual([], results)
        
        
    def testCreateTrainRecord(self):
        date_rec = datetime.strptime("2026-01-08 04:05:06:-0400", "%Y-%m-%d %H:%M:%S:%z")
        data = {
            "date_rec": date_rec,
            "station_id": 2,
            "frame_sync": "beep",
            "command": "boop",
            "checkbits": "C1",
            "parity": "T2",
            "unit_addr": "CT12"
        }
        
        # Test recovery request creation
        result_id, result_recov = self.repo.create_train_record(data, None)
        self.assertEqual(8, result_id)
        self.assertEqual(True, result_recov)
        
        # Test non-recovery request creation
        data["date_rec"] = None
        result_id, result_recov = self.repo.create_train_record(data, date_rec)
        self.assertEqual(9, result_id)
        self.assertEqual(False, result_recov)
        
        # Test datetime never provided exceptions
        with self.assertRaises(RepositoryInvalidArgumentError):
            self.repo.create_train_record(data, None)
            
        # Test "execute" return exceptions
        with patch.object(Session, "execute") as mock:
            mock.return_value.scalar_one_or_none.return_value = None
            
            with self.assertRaises(RepositoryInternalError):
                self.repo.create_train_record(data, date_rec)
        
        
    def testGetRecentStationRecords(self):
        expected = [self.repo.get(i) for i in range(2, 8)]
        expected.remove(expected[4])
        results = self.repo.get_recent_station_records(1)
        self.assertListEqual(expected, results)
        
        
    def testGetRecordCollation(self):
        expected = [
            {
                "id": 7,
                "date_rec": "2026-08-16 20:17:11",
                "first_seen": "2026-08-16 20:17:11",
                "last_seen": "2026-08-16 20:17:11",
                "duration": "0:00:00",
                "occurrence_count": "1",
                "station_name": "test station1" ,
                "unit_addr": "1234",
                "verified": False
            },
            {
                "id": 6,
                "date_rec": "2021-08-16 20:17:11",
                "first_seen": "2021-08-16 20:17:11",
                "last_seen": "2021-08-16 20:17:11",
                "duration": "0:00:00",
                "occurrence_count": "1",
                "station_name": "test station2",
                "unit_addr": "9910",
                "verified": False
            },
            {
                "id": 5,
                "date_rec": "2021-08-16 20:16:11",
                "first_seen": "2021-08-16 20:14:11",
                "last_seen": "2021-08-16 20:16:11",
                "duration": "0:02:00",
                "occurrence_count": "3",
                "station_name": "test station1",
                "unit_addr": "9910",
                "verified": False
            },
            {
                "id": 2,
                "date_rec": "2001-02-04 01:23:45",
                "first_seen": "2001-02-04 01:23:45",
                "last_seen": "2001-02-04 01:23:45",
                "duration": "0:00:00",
                "occurrence_count": "1",
                "station_name": "test station1",
                "unit_addr": "5678",
                "verified": False
            },
            {
                "id": 1,
                "date_rec": "1999-01-08 04:10:21",
                "first_seen": "1999-01-08 04:10:21",
                "last_seen": "1999-01-08 04:10:21",
                "duration": "0:00:00",
                "occurrence_count": "1",
                "station_name": "test station1",
                "unit_addr": "1234",
                "verified": False
            }
        ]

        # All results with only one partition
        results = self.repo.get_record_collation(1, 250, None)
        valid, message = collation_valid({"results": expected, "totalPages": 1}, results)
        self.assertTrue(valid, message)
        
        # Portion of results with multiple partitions
        results = self.repo.get_record_collation(1, 2, None)
        valid, message = collation_valid({"results": expected[0:2], "totalPages": 3}, results)
        self.assertTrue(valid, message)
        
        # Portion of result with last partition
        results = self.repo.get_record_collation(3, 2, None)
        valid, message = collation_valid({"results": expected[4:], "totalPages": 3}, results)
        self.assertTrue(valid, message)  
        
        # Test getting no records
        results = self.repo.get_record_collation(3, 3, None)
        self.assertEqual({"results": [], "totalPages": 2}, results)      
        
        # Test getting verified records
        for i in range(1, 6):
            self.repo.verify_record(i, 1, "cheese balls")
        for i in range(2, 5):
            expected[i]["symbol_id"] = 1
            expected[i]["verified"] = True 
            expected[i]["locomotive_num"] = "cheese balls"  
            expected[i]["symb_name"] = "Test Symbol1"
        
        # Verified record results
        results = self.repo.get_record_collation(1, 250, True)
        valid, message = collation_valid({"results": expected[2:5], "totalPages": 1}, results)
        self.assertTrue(valid, message)
        
        # Unverfied record results
        results = self.repo.get_record_collation(1, 250, False)
        valid, message = collation_valid({"results": expected[:2], "totalPages": 1}, results)
        self.assertTrue(valid, message)
        
    
    def testGetRecordCollationExceptions(self):
        # Test that exception is handled in collation step
        with patch.object(Session, "execute") as mock_session:
            mock_session.return_value.all.side_effect = SQLAlchemyError
            with self.assertRaises(RepositoryInternalError):
                self.repo.get_record_collation(1, 250, None)
            
        # Test that exception is handled in counting step
        with patch.object(Session, "execute") as mock_session:
            mock_session.return_value.scalar_one.side_effect = SQLAlchemyError
            with self.assertRaises(RepositoryInternalError):
                self.repo.get_record_collation(1, 250, None)
        
        # Test that exception is handled in parsing step
        with patch("backend.src.db.hot_repo.ceil", side_effect=ValueError()):
            with self.assertRaises(RepositoryParsingError):
                self.repo.get_record_collation(1, 250, None)
        
    
if __name__ == '__main__':
    unittest.main()