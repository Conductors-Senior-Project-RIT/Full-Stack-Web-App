from pprint import pprint
import unittest
import math
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import Session


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
                'arm_status': 'unknown',
                'battery_charge': 'unknown',
                'battery_cond': 'unknown',
                'brake_pressure': 'unknown',
                'date_rec': '2025-05-25 05:20:00',
                'id': 8,
                'marker_light': 'unknown',
                'motion': 'unknown',
                'signal_strength': 0.0,
                'station_name': 'test station1',
                'symb_name': 'Test Symbol1',
                'turbine': 'unknown',
                'unit_addr': '1234',
                'verified': False
            },
            {
                'arm_status': 'unknown',
                'battery_charge': 'unknown',
                'battery_cond': 'unknown',
                'brake_pressure': 'unknown',
                'date_rec': '2025-03-25 05:20:00',
                'id': 7,
                'marker_light': 'unknown',
                'motion': 'unknown',
                'signal_strength': 0.0,
                'station_name': 'test station1',
                'symb_name': 'Test Symbol1',
                'turbine': 'unknown',
                'unit_addr': '1234',
                'verified': False
            },
            {
                'arm_status': 'unknown',
                'battery_charge': 'unknown',
                'battery_cond': 'unknown',
                'brake_pressure': 'unknown',
                'date_rec': '2025-03-25 05:15:00',
                'id': 6,
                'marker_light': 'unknown',
                'motion': 'unknown',
                'signal_strength': 0.0,
                'station_name': 'test station1',
                'symb_name': None,
                'turbine': 'unknown',
                'unit_addr': '1234',
                'verified': False
            },
            {
                'arm_status': 'unknown',
                'battery_charge': 'unknown',
                'battery_cond': 'unknown',
                'brake_pressure': 'unknown',
                'date_rec': '2025-03-25 05:10:00',
                'id': 5,
                'marker_light': 'unknown',
                'motion': 'unknown',
                'signal_strength': 0.0,
                'station_name': 'test station2',
                'symb_name': None,
                'turbine': 'unknown',
                'unit_addr': '1234',
                'verified': False
            },
            {
                'arm_status': 'unknown',
                'battery_charge': 'unknown',
                'battery_cond': 'unknown',
                'brake_pressure': 'unknown',
                'date_rec': '2025-03-25 05:05:00',
                'id': 4,
                'marker_light': 'unknown',
                'motion': 'unknown',
                'signal_strength': 0.0,
                'station_name': 'test station1',
                'symb_name': None,
                'turbine': 'unknown',
                'unit_addr': '1234',
                'verified': False
            },
            {
                'arm_status': 'unknown',
                'battery_charge': 'unknown',
                'battery_cond': 'unknown',
                'brake_pressure': 'unknown',
                'date_rec': '2025-03-25 05:00:00',
                'id': 3,
                'marker_light': 'unknown',
                'motion': 'unknown',
                'signal_strength': 0.0,
                'station_name': 'test station1',
                'symb_name': None,
                'turbine': 'unknown',
                'unit_addr': '1234',
                'verified': False
            },
            {
                'arm_status': 'unknown',
                'battery_charge': 'unknown',
                'battery_cond': 'unknown',
                'brake_pressure': 'unknown',
                'date_rec': '2003-02-05 06:53:08',
                'id': 2,
                'marker_light': 'unknown',
                'motion': 'unknown',
                'signal_strength': 0.0,
                'station_name': 'test station1',
                'symb_name': None,
                'turbine': 'unknown',
                'unit_addr': '1337',
                'verified': False
            },
            {
                'arm_status': 'unknown',
                'battery_charge': 'unknown',
                'battery_cond': 'unknown',
                'brake_pressure': 'unknown',
                'date_rec': '1999-01-08 04:05:06',
                'id': 1,
                'marker_light': 'unknown',
                'motion': 'unknown',
                'signal_strength': 0.0,
                'station_name': 'test station1',
                'symb_name': 'Test Symbol1',
                'turbine': 'unknown',
                'unit_addr': '727',
                'verified': False
            }
        ]
        
        results = self.repo.get_train_history(-1, 1, 250)
        self.assertEqual({"results": expected, "totalPages": 1}, results)
        
        results = self.repo.get_train_history(1, None, None)
        self.assertEqual([expected[-1]], results)
        
        
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
        

if __name__ == '__main__':
    unittest.main()