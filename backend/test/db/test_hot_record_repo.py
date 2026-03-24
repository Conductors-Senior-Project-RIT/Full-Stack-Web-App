from pprint import pprint
import unittest
import math
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import Session


from backend.src.db.db_core.repository import RepositoryInternalError, RepositoryInvalidArgumentError, RepositoryNotFoundError, RepositoryParsingError
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
        # Do we even keep this method??
        # expected = [self.repo.get(i) for i in range(4)]
        # results = self.repo.get_train_history()
        pass
        
    def testCreateTrainRecord(self):
        date_rec = datetime.strptime("2026-01-08 04:05:06:-0400", "%Y-%m-%d %H:%M:%S:%z")
        data = {
            "date_rec": date_rec,
            "station_recorded": 2,
            "frame_sync": "beep",
            "command": "boop",
            "checkbits": "C1",
            "parity": "T2",
            "unit_addr": "CT12"
        }
        
        # Test recovery request creation
        result_obj, result_recov = self.repo.create_train_record(data, None, False)
        self.assertEqual(8, result_obj["id"])
        self.assertEqual(date_rec, result_obj["date_rec"])
        self.assertEqual(True, result_recov)
        
        # Test non-recovery request creation
        data["date_rec"] = None
        result_obj, result_recov = self.repo.create_train_record(data, date_rec, False)
        self.assertEqual(9, result_obj["id"])
        self.assertEqual(date_rec, result_obj["date_rec"])
        self.assertEqual(False, result_recov)
        
        # Test datetime never provided exceptions
        with self.assertRaises(RepositoryInvalidArgumentError):
            self.repo.create_train_record(data, None, False)
            
        # Test "create" return exceptions
        with patch.object(HOTRepository, "create") as mock:
            mock.return_value = []
            
            with self.assertRaises(RepositoryInternalError):
                self.repo.create_train_record(data, date_rec, True)
                
            mock.return_value = [{"id": 6}, {"id": 7}]
            with self.assertRaises(RepositoryInternalError):
                self.repo.create_train_record(data, date_rec, True)
        
        
    def testGetRecentStationRecords(self):
        expected = [self.repo.get(i) for i in range(2, 8)]
        expected.remove(expected[4])
        results = self.repo.get_recent_station_records(1)
        self.assertListEqual(expected, results)
        
        
    def testGetRecordCollation(self):
        all_expected = {
            'results': [
                {
                    'date_rec': '2026-08-16 20:17:11',
                    'duration': '0000-00-00 00:00:00',
                    'first_seen': '2026-08-16 20:17:11',
                    'id': 7,
                    'last_seen': '2026-08-16 20:17:11',
                    'locomotive_num': 'unknown',
                    'occurrence_count': 1,
                    'signal_strength': 0.0,
                    'station_name': 'test station1',
                    'symb_name': None,
                    'symbol_id': None,
                    'unit_addr': '1234',
                    'verified': False
                },
                {
                    'date_rec': '2021-08-16 20:17:11',
                    'duration': '0000-00-00 00:00:00',
                    'first_seen': '2021-08-16 20:17:11',
                    'id': 6,
                    'last_seen': '2021-08-16 20:17:11',
                    'locomotive_num': 'unknown',
                    'occurrence_count': 1,
                    'signal_strength': 0.0,
                    'station_name': 'test station2',
                    'symb_name': None,
                    'symbol_id': None,
                    'unit_addr': '9910',
                    'verified': False
                },
                {
                    'date_rec': '2021-08-16 20:16:11',
                    'duration': '0000-00-00 00:02:00',
                    'first_seen': '2021-08-16 20:14:11',
                    'id': 5,
                    'last_seen': '2021-08-16 20:16:11',
                    'locomotive_num': 'unknown',
                    'occurrence_count': 3,
                    'signal_strength': 0.0,
                    'station_name': 'test station1',
                    'symb_name': None,
                    'symbol_id': None,
                    'unit_addr': '9910',
                    'verified': False
                },
                {  
                    'date_rec': '2001-02-04 01:23:45',
                    'duration': '0000-00-00 00:00:00',
                    'first_seen': '2001-02-04 01:23:45',
                    'id': 2,
                    'last_seen': '2001-02-04 01:23:45',
                    'locomotive_num': 'unknown',
                    'occurrence_count': 1,
                    'signal_strength': 0.0,
                    'station_name': 'test station1',
                    'symb_name': None,
                    'symbol_id': None,
                    'unit_addr': '5678',
                    'verified': False
                },
                {  
                    'date_rec': '1999-01-08 04:10:21',
                    'duration': '0000-00-00 00:00:00',
                    'first_seen': '1999-01-08 04:10:21',
                    'id': 1,
                    'last_seen': '1999-01-08 04:10:21',
                    'locomotive_num': 'unknown',
                    'occurrence_count': 1,
                    'signal_strength': 0.0,
                    'station_name': 'test station1',
                    'symb_name': None,
                    'symbol_id': None,
                    'unit_addr': '1234',
                    'verified': False
                }
            ],
            'totalPages': 1
        }
        
        result = self.repo.get_record_collation(1, 250)
        self.assertEqual(all_expected, result)
        
        result = self.repo.get_record_collation(1, 2)
        self.assertEqual({"results": all_expected["results"][0:2], "totalPages": 3}, result)
        
        result = self.repo.get_record_collation(3, 2)
        self.assertEqual({"results": [all_expected["results"][4]], "totalPages": 3}, result)
            
    def testGetRecordCollationException(self):
        with patch.object(Session, "execute") as mock:
            mock.return_value.all.side_effect = SQLAlchemyError
            with self.assertRaises(RepositoryInternalError):
                self.repo.get_record_collation(1, 250)
        
        with patch.object(Session, "execute") as mock:
            mock.return_value.scalar_one.side_effect = SQLAlchemyError
            with self.assertRaises(RepositoryInternalError):
                self.repo.get_record_collation(1, 250)
                
        with patch("backend.src.db.hot_repo.ceil", side_effect=TypeError()) as mock:
            with self.assertRaises(RepositoryParsingError):
                self.repo.get_record_collation(1, 250)
                mock.assert_called_once()
                
                
    ###################################
    ##  get_records_by_verification  ##
    ###################################
    def testGetRecordsByVerification(self):
        test_results = [
            {
                'date_rec': '2026-08-16 20:17:11',
                'duration': '0000-00-00 00:00:00',
                'first_seen': '2026-08-16 20:17:11',
                'id': 7,
                'last_seen': '2026-08-16 20:17:11',
                'occurrence_count': 1,
                'signal_strength': 0.0,
                'station_name': 'test station1',
                'symbol_id': None,
                'unit_addr': '1234',
                'verified': False
            },
            {
                'date_rec': '1999-01-08 04:10:21',
                'duration': '0000-00-00 00:00:00',
                'first_seen': '1999-01-08 04:10:21',
                'id': 1,
                'last_seen': '1999-01-08 04:10:21',
                'occurrence_count': 1,
                'signal_strength': 0.0,
                'station_name': 'test station1',
                'symbol_id': None,
                'unit_addr': '1234',
                'verified': False
            },
            {
                'date_rec': '2001-02-04 01:23:45',
                'duration': '0000-00-00 00:00:00',
                'first_seen': '2001-02-04 01:23:45',
                'id': 2,
                'last_seen': '2001-02-04 01:23:45',
                'occurrence_count': 1,
                'signal_strength': 0.0,
                'station_name': 'test station1',
                'symbol_id': None,
                'unit_addr': '5678',
                'verified': False
            },
            {
                'date_rec': '2021-08-16 20:17:11',
                'duration': '0000-00-00 00:00:00',
                'first_seen': '2021-08-16 20:17:11',
                'id': 6,
                'last_seen': '2021-08-16 20:17:11',
                'occurrence_count': 1,
                'signal_strength': 0.0,
                'station_name': 'test station2',
                'symbol_id': None,
                'unit_addr': '9910',
                'verified': False
            },
            {
                'date_rec': '2021-08-16 20:16:11',
                'duration': '0000-00-00 00:02:00',
                'first_seen': '2021-08-16 20:14:11',
                'id': 5,
                'last_seen': '2021-08-16 20:16:11',
                'occurrence_count': 3,
                'signal_strength': 0.0,
                'station_name': 'test station1',
                'symbol_id': None,
                'unit_addr': '9910',
                'verified': False
            }
        ]
            
        results = self.repo.get_record_collation(1, 250, False)
        self.assertEqual({"results": test_results, "totalPages": 1}, results)
        
        results = self.repo.get_record_collation(1, 2, False)
        self.assertEqual({"results": test_results[0:2], "totalPages": 4}, results)
        
        results = self.repo.get_record_collation(3, 2, False)
        self.assertEqual({"results": test_results[4:], "totalPages": 4}, results)
        
        for i in range(4, 7):
            self.repo.verify_record(i, 1, "cheese balls")
        for i in range(3, 5):
            test_results[i]["symbol_id"] = 1
            test_results[i]["verified"] = True    
        
        results = self.repo.get_record_collation(1, 250, True)
        self.assertEqual({"results": test_results[3:5], "totalPages": 1}, results)
        
    def testGetRecordsByVerificationException(self):
        with self.assertRaises(RepositoryInvalidArgumentError):
            self.repo.get_record_collation(1, 250, "Taco")
        
    
if __name__ == '__main__':
    unittest.main()