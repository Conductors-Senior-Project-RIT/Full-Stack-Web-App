import unittest
from datetime import datetime
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import Session

from backend.test.db.test_utils import collation_valid, compare_results_ordered
from backend.src.db.db_core.exceptions import RepositoryInternalError, RepositoryInvalidArgumentError, RepositoryParsingError
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
        
    
    #########################
    ##  get_train_history  ##
    #########################
    def testGetTrainHistory(self):
        expected_record = self.repo.get(1)
        expected_record["station_name"] = "test station1"
        expected_record["symb_name"] = None
        expected_record["date_rec"] = str(expected_record["date_rec"])
        
        results = self.repo.get_train_history(1)
        valid, msg = compare_results_ordered([results], [expected_record])
        self.assertTrue(valid, msg)
        
        results = self.repo.get_train_history(17)
        self.assertIsNone(results)
        
        
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