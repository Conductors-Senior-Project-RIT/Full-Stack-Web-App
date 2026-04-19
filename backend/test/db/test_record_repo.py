from datetime import datetime
import pprint
import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError, SQLAlchemyError
from sqlalchemy.orm.session import Session
from yaml import warnings

from test_utils import TestTrainRecord, TestRepository, return_test_data

from backend.database import db
from backend.src.db.db_core.models import Base, BaseRecord
from backend.src.db.base_record_repo import RecordRepository
from backend.src.db.db_core.exceptions import RepositoryExistingRowError, RepositoryInternalError, RepositoryInvalidArgumentError, RepositoryNotFoundError, RepositoryParsingError
from backend.src.db.db_core.repository import BaseRepository
from backend.src.global_core.exceptions import LayerError
from backend.test.base_test_case import BaseTestCase



class TestRecordRepository(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with db.engine.connect() as conn:
            conn.execute(text("TRUNCATE trainrecords RESTART IDENTITY CASCADE"))
            conn.commit()
    
    def setUp(self):
        super().setUp()
        self.repo = TestRepository(self.session)
        
        # Reset sequence before inserting so ids start at 1
        self.session.execute(text(
            "SELECT setval(pg_get_serial_sequence('trainrecords', 'id'), coalesce(MAX(id), 1), false) FROM trainrecords"
        ))
        self.test_data = return_test_data()
        self.session.add_all(self.test_data)
        self.session.flush()
    
    
    def testGetTotalRecordCount(self):
        self.assertEqual(len(self.test_data), self.repo.get_total_record_count())
        
    
    def testGetTrainRecord(self):
        # Test that successful retrieval
        for i in [1, "1"]:
            result = self.repo.get(i)
            self.assertDictEqual(self.test_data[0]._asdict(), result)
        
        # Test invalid id
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.get(-1)
            
            
    def testGetUnitRecordIds(self):
        # Check that valid list of ids are returned
        test_ret = [1, 3]
        result = self.repo.get_unit_record_ids("1111", False)
        self.assertListEqual(test_ret, result)
        
        # Check that valid most recent id returned
        result = self.repo.get_unit_record_ids("1111", True)
        self.assertEqual(3, result)
        
        # Test that an exception is raised when nothing is found
        with self.assertRaises(RepositoryNotFoundError):
            result = self.repo.get_unit_record_ids("unit", True)
            
            
    def testGetRecentTrains(self):
        # Test successful retrieval of new record
        results = self.repo.get_recent_trains("1111", 1)
        expected = [self.test_data[2]]
        self.assertListEqual(expected, results)
        
        # Test failed retrieval of records
        results = self.repo.get_recent_trains("bruh", 1)
        self.assertListEqual([], results)

            
    def testAddNewPin(self):
        # Test successful pin update
        result_id = self.repo.add_new_pin(4, "1111")
        self.assertListEqual([3], result_id)
        
        result_id = self.repo.add_new_pin(3, "1111")
        self.assertListEqual([], result_id)
            
            
    ######################################
    ##  get_record_column_by_unit_addr  ##
    ###################################### 
    def _run_get_record_case(self, unit_addr, column, position, recent, expected):
        result = self.repo.get_record_column_by_unit_addr(unit_addr, column, position, recent)
        self.assertIsInstance(result, type(expected))
        self.assertEqual(expected, result)
          
    def testGetRecordSymbol(self):
        test_cases = [
            # Below are the tests for symbol_id
            ("2222", "symbol_id", True, [2]),
            ("2222", "symbol_id", False, [2]),
            ("2222", "symbol_id", None, [2, 2]), 
            # Below are the tests for engine_num
            ("1111", "engine_num", True, [1]),
            ("1111", "engine_num", False, [1]),
            ("1111", "engine_num", None, [1, 1]), 
            # Below are the not found cases
            ("0000", "engine_num", True, []),
            ("0000", "engine_num", False, []),
            ("0000", "engine_num", None, [])
        ]
        
        for unit, col, rec, exp in test_cases:
            # If this fails, the error message will include these params
            with self.subTest(unit=unit, col=col, rec=rec, exp=exp):
                result = self.repo.get_record_column_by_unit_addr(unit, col, rec)
                self.assertEqual(exp, result)
            
        # Make sure exception raised if not valid column
        with self.assertRaises(RepositoryInvalidArgumentError):
            self.repo.get_record_column_by_unit_addr("5545", "Bob")
            
        with self.assertRaises(RepositoryParsingError):
            self.repo.get_record_column_by_unit_addr("1111", "engine_num", "Bob")
        
    
    # ############################
    # ##  update_signal_values  ##
    # ############################
    def testUpdateSignalValues(self):
        test_symbol = None
        test_engine = None
        
        # Test no values change
        result = self.repo.update_signal_values(1, test_symbol, test_engine)
        self.assertEqual(None, result)
        
        test_cases = [
            (2, None),
            (None, 2),
            (1, 1)
        ]
        
        for sym, eng in test_cases:
            with self.subTest(sym=sym, eng=eng):
                updated = self.repo.update_signal_values(1, sym, eng, False)
                self.session.add(updated)
                self.session.flush()
                
                result = self.repo.get(1, False)
                self.assertEqual(updated, result)

    
    ###########################
    ##  get_station_records  ##
    ###########################
    def testGetStationRecords(self):
        self.maxDiff = None
        # All tests will be executed with recent=False in this class
        expected = [self.test_data[0], self.test_data[2]]
        result = self.repo.get_station_records(1)
        self.assertListEqual(expected, result)
        
        with patch.object(Session, "execute") as mock:
            mock.side_effect = SQLAlchemyError
            with self.assertRaises(RepositoryInternalError):
                self.repo.get_station_records(1)
        
        
    #####################
    ##  verify_record  ##
    #####################
    def testVerifyRecord(self):
        sym, loc = 2, "RG00"
        
        # Get the updated instance in session
        updated = self.repo.verify_record(3, sym, loc, False)
        self.session.add(updated)
        self.session.flush()
        
        # Make sure the changes are correctly reflected in the session
        result = self.repo.get(3, False)
        self.assertEqual(updated, result)
        
        with patch.object(RecordRepository, "update_with_pk") as mock:
            mock.side_effect = SQLAlchemyError
            with self.assertRaises(RepositoryInternalError):
                self.repo.verify_record(3, sym, loc)
        
        
    ################################
    ##  get_records_in_timeframe  ##
    ################################
    def testGetRecordsInTimeframe(self):
        self.maxDiff = None
        expected = [
            {
                'id': 4, 
                'date_rec': self.test_data[3].date_rec, 
                'unit_addr': '2222', 
                'station_name': 'test station2',
                'symb_name': 'Test Symbol2', 
                'engine_num': 2, 
                'locomotive_num': 'CY00',
                'Data_type': 'TRAIN'
            },
            {
                'id': 3, 
                'date_rec': self.test_data[2].date_rec, 
                'unit_addr': '1111', 
                'station_name': 'test station1',
                'symb_name': 'Test Symbol1', 
                'engine_num': 1, 
                'locomotive_num': 'EL00',
                'Data_type': 'TRAIN'
            },
            {
                'id': 2,
                'date_rec': self.test_data[1].date_rec,
                'unit_addr': '2222', 
                'station_name': 'test station2',
                'symb_name': 'Test Symbol2', 
                'engine_num': 2, 
                'locomotive_num': 'TG00',
                'Data_type': 'TRAIN'
            },
            {
                'id': 1,
                'date_rec': self.test_data[0].date_rec,
                'unit_addr': '1111', 
                'station_name': 'test station1',
                'symb_name': 'Test Symbol1', 
                'engine_num': 1, 
                'locomotive_num': 'CT00',
                'Data_type': 'TRAIN'
            }
        ]
        dt = datetime.strptime("1998-01-08 04:05:06", "%Y-%m-%d %H:%M:%S")
        results = self.repo.get_records_in_timeframe(-1, dt, False)
        self.assertListEqual(expected[2:], results)
        
        results = self.repo.get_records_in_timeframe(1, dt, False)
        self.assertListEqual([expected[3]], results)
        
        results = self.repo.get_records_in_timeframe(-1, dt, True)
        self.assertListEqual(expected[:2], results)
        
        results = self.repo.get_records_in_timeframe(1, dt, True)
        self.assertListEqual([expected[1]], results)
        
        results = self.repo.get_records_in_timeframe(1, dt)
        self.assertListEqual(expected[1::2], results)
        
        with patch.object(Session, "execute") as mock:
            mock.side_effect = SQLAlchemyError
            with self.assertRaises(RepositoryInternalError):
                self.repo.get_records_in_timeframe(-1, dt, True)
                
                
if __name__ == "__main__":
    unittest.main()
            
        