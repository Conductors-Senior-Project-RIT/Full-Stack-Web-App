from pprint import pprint
import unittest
import math
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import Session

from record_tests import collation_valid, compare_results
from backend.src.db.db_core.exceptions import RepositoryInternalError, RepositoryInvalidArgumentError, RepositoryNotFoundError, RepositoryParsingError
from backend.database import db
from backend.src.db.eot_repo import EOTRepository
from backend.test.base_test_case import BaseTestCase


class TestEOTRecordRepository(BaseTestCase):
    def setUp(self):
        self.session = db.session
        self.repo = EOTRepository(self.session)

        
    def tearDown(self):
        self.session.rollback() # revert changes made from every test_method ran
        self.session.close()


    ###############
    ##  Getters  ##
    ###############
    def testGetters(self):
        self.assertEqual("EOT Record", self.repo.get_record_name())
        self.assertEqual("eot", self.repo.get_record_identifier())


    def testGetTrainHistory(self):
        expected = [
            {
                'id': 8,
                'date_rec': '2025-05-25 05:20:00',
                'station_name': 'test station1',
                'symb_name': 'Test Symbol1'
            },
            {
                'id': 7,
                'date_rec': '2025-03-25 05:20:00',
                'station_name': 'test station1',
                'symb_name': 'Test Symbol1'
            },
            {
                'id': 6,
                'date_rec': '2025-03-25 05:15:00',
                'station_name': 'test station1',
                'symb_name': None
            },
            {
                'id': 5,
                'date_rec': '2025-03-25 05:10:00',
                'station_name': 'test station2',
                'symb_name': None
            },
            {
                'id': 4,
                'date_rec': '2025-03-25 05:05:00',
                'station_name': 'test station1',
                'symb_name': None
            },
            {
                'id': 3,
                'date_rec': '2025-03-25 05:00:00',
                'station_name': 'test station1',
                'symb_name': None
            },
            {
                'id': 2,
                'date_rec': '2003-02-05 06:53:08',
                'station_name': 'test station1',
                'symb_name': None
            },
            {
                'id': 1,
                'date_rec': '1999-01-08 04:05:06',
                'station_name': 'test station1',
                'symb_name': 'Test Symbol1'
            }
        ]
        
        # Test that getting all records works
        results = self.repo.get_train_history(-1, 1, 250)
        valid, message = collation_valid({"results": expected, "totalPages": 1}, results)
        self.assertTrue(valid, message)
        
        # Test that getting a full page of records works
        results = self.repo.get_train_history(-1, 1, 2)
        valid, message = collation_valid({"results": expected[:2], "totalPages": 4}, results)
        self.assertTrue(valid, message)

        # Test that getting a partial page of records works
        results = self.repo.get_train_history(-1, 3, 3)
        valid, message = collation_valid({"results": expected[-2:], "totalPages": 3}, results)
        self.assertTrue(valid, message)
        
        # Test bot getting records on an exceeding page
        results = self.repo.get_train_history(-1, 4, 3)
        self.assertDictEqual({"results": [], "totalPages": 3}, results)
        
        # Test that getting a single record works
        results = self.repo.get_train_history(1, None, None)
        valid, message = compare_results([expected[-1]], results)
        self.assertTrue(valid, message)
        
        # Test not finding record
        results = self.repo.get_train_history(17, None, None)
        self.assertEqual([], results)
        
        
    def testCreateTrainRecord(self):
        date_rec = datetime.strptime("2026-01-08 04:05:06", "%Y-%m-%d %H:%M:%S")
        data = {
            "date_rec": date_rec,
            "station_id": 2,
            "unit_addr": "CT12",
            "brake_pressure": "heavy",
            "motion": "moving",
            "marker_light": "bright",
            "turbine": "spinning",
            "battery_cond": "blowing up",
            "battery_charge": "dead",
            "arm_status": "fully loaded",
            "signal_strength": 1.0,
            "symbol_id": None
        }
        
        # Test recovery request creation
        result_id, result_recov = self.repo.create_train_record(data, None) 
        self.assertEqual(9, result_id)
        self.assertTrue(result_recov)
        
        # Test non-recovery request creation
        data["date_rec"] = None
        result_id, result_recov = self.repo.create_train_record(data, date_rec)
        self.assertEqual(10, result_id)
        self.assertFalse(result_recov)
        
        # Test datetime never provided exceptions
        with self.assertRaises(RepositoryInvalidArgumentError):
            self.repo.create_train_record(data, None)
            
        # Test "execute" return exceptions
        with patch.object(Session, "execute") as mock:
            mock.return_value.scalar_one_or_none.return_value = None
            
            with self.assertRaises(RepositoryInternalError):
                self.repo.create_train_record(data, date_rec)
                
    
    def testGetRecentStationRecords(self):
        expected = [self.repo.get(i) for i in range(7, 9)]
        results = self.repo.get_recent_station_records(1)
        self.assertListEqual(expected, results)
        
        
    def testGetRecordCollation(self):
        expected = [
            {
                'id': 8,
                'date_rec': '2025-05-25 05:20:00',
                'first_seen': '2025-05-25 05:20:00',
                'last_seen': '2025-05-25 05:20:00',
                'duration': '0:00:00',
                'occurrence_count': '1',
                'station_name': 'test station1',
                'unit_addr': '1234',
                'symbol_id': 1,
                'symbol_name': 'Test Symbol1',
            },
            {
                'id': 7,
                'date_rec': '2025-03-25 05:20:00',
                'first_seen': '2025-03-25 05:15:00',
                'last_seen': '2025-03-25 05:20:00',
                'duration': '0:05:00',
                'occurrence_count': '2',
                'station_name': 'test station1',
                'unit_addr': '1234',
                'symbol_id': 1,
                'symbol_name': 'Test Symbol1',
            },
            {
                'id': 5,
                'date_rec': '2025-03-25 05:10:00',
                'first_seen': '2025-03-25 05:10:00',
                'last_seen': '2025-03-25 05:10:00',
                'duration': '0:00:00',
                'occurrence_count': '1',
                'station_name': 'test station2',
                'unit_addr': '1234',
                'symbol_id': None,
                'symbol_name': None,
            },
            {
                'id': 4,
                'date_rec': '2025-03-25 05:05:00',
                'first_seen': '2025-03-25 05:00:00',
                'last_seen': '2025-03-25 05:05:00',
                'duration': '0:05:00',
                'occurrence_count': '2',
                'station_name': 'test station1',
                'unit_addr': '1234',
                'symbol_id': None,
                'symbol_name': None,
            },
            {
                'id': 2,
                'date_rec': '2003-02-05 06:53:08',
                'first_seen': '2003-02-05 06:53:08',
                'last_seen': '2003-02-05 06:53:08',
                'duration': '0:00:00',
                'occurrence_count': '1',
                'station_name': 'test station1',
                'unit_addr': '1337',
                'symbol_id': None,
                'symbol_name': None,
            },
            {
                'id': 1,
                'date_rec': '1999-01-08 04:05:06',
                'first_seen': '1999-01-08 04:05:06',
                'last_seen': '1999-01-08 04:05:06',
                'duration': '0:00:00',
                'occurrence_count': '1',
                'station_name': 'test station1',
                'unit_addr': '727',
                'symbol_id': 1,
                'symbol_name': 'Test Symbol1',
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
        results = self.repo.get_record_collation(2, 4, None)
        valid, message = collation_valid({"results": expected[4:], "totalPages": 2}, results)
        self.assertTrue(valid, message)
        
        # Test getting no records
        results = self.repo.get_record_collation(3, 4, None)
        self.assertEqual({"results": [], "totalPages": 2}, results)
        
        # Test getting verified records
        for i in range(1, 6):
            self.repo.verify_record(i, 1, "cheese balls")
        for i in range(2, len(expected)):
            expected[i]["symbol_id"] = 1
            expected[i]["verified"] = True 
            expected[i]["locomotive_num"] = "cheese balls"  
            expected[i]["symbol_name"] = "Test Symbol1"
        
        # Verified record results
        results = self.repo.get_record_collation(1, 250, True)
        valid, message = collation_valid({"results": expected[2:], "totalPages": 1}, results)
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
        with patch("backend.src.db.eot_repo.ceil", side_effect=ValueError()):
            with self.assertRaises(RepositoryParsingError):
                self.repo.get_record_collation(1, 250, None)
            

if __name__ == '__main__':
    unittest.main()