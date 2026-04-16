from datetime import datetime
import unittest
from unittest.mock import patch

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import Session

from backend.database import db
from backend.src.db.db_core.models import Base, BaseRecord
from backend.src.db.base_record_repo import RecordRepository
from backend.src.db.db_core.exceptions import RepositoryInternalError, RepositoryInvalidArgumentError, RepositoryNotFoundError, RepositoryParsingError
from backend.src.db.db_core.repository import BaseRepository
from backend.test.base_test_case import BaseTestCase


class TestTrainRecord(BaseRecord):
    __tablename__ = "trainrecords"


class TestRepository(RecordRepository):  
    def __init__(self, session):
        super().__init__(TestTrainRecord, session, "Train Record", "train")
      
    def get_train_history(self, id, page, num_results):
        pass

    def create_train_record(self, args, datetime_string):
        pass

    def get_recent_station_records(self, station_id):
        pass

    def get_record_collation(self, page):
        pass

    def get_records_by_verification(self, page, verified):
        pass


class TestBaseRepositories(BaseTestCase):
    def setUp(self):
        self.session = db.session
        TestTrainRecord.__table__.drop(bind=db.engine, checkfirst=True)
        TestTrainRecord.__table__.create(bind=db.engine, checkfirst=True)
        self.repo = TestRepository(self.session)
        
        self.test_data = [
            TestTrainRecord(
                id=1,
                date_rec=datetime.strptime("1999-01-08 04:05:06", "%Y-%m-%d %H:%M:%S"),
                station_recorded=1,
                most_recent=False,
                unit_addr="1111",
                symbol_id=1,
                engine_num=1,
                locomotive_num="CT00",
                verified=True,
                signal_strength=0.0
            ),
            TestTrainRecord(
                id=2,
                date_rec=datetime.strptime("2003-02-05 06:53:08", "%Y-%m-%d %H:%M:%S"),
                station_recorded=2,
                most_recent=False,
                unit_addr="2222",
                symbol_id=2,
                engine_num=2,
                locomotive_num="TG00",
                verified=True,
                signal_strength=0.0
            ),
            TestTrainRecord(
                id=3,
                date_rec=datetime.now(),
                station_recorded=1,
                most_recent=True,
                unit_addr="1111",
                symbol_id=1,
                engine_num=1,
                locomotive_num="EL00",
                verified=False,
                signal_strength=0.0
            ),
            TestTrainRecord(
                id=4,
                date_rec=datetime.now(),
                station_recorded=2,
                most_recent=True,
                unit_addr="2222",
                symbol_id=2,
                engine_num=2,
                locomotive_num="CY00",
                verified=False,
                signal_strength=0.0
            )
        ]
        
        self.session.add_all(self.test_data)
        self.session.flush()
        
        
    def tearDown(self):
        self.session.rollback() # revert changes made from every test_method ran
        self.session.close()
        
        
    ###################################
    ##  TESTS FOR RECORD REPOSITORY  ##
    ###################################
    
    # def testGetters(self):
    #     self.assertEqual("Train Record", self.repo.get_record_name())
    #     self.assertEqual("train", self.repo.get_record_identifier())
    
    
    # def testGetTotalRecordCount(self):
    #     self.assertEqual(len(self.test_data), self.repo.get_total_record_count())
    
    
    # def testGetTrainRecord(self):
    #     # Test that successful retrieval
    #     for i in [1, "1"]:
    #         result = self.repo.get(i)
    #         self.assertDictEqual(self.test_data[0]._asdict(), result)
        
    #     # Test invalid id
    #     with self.assertRaises(RepositoryNotFoundError):
    #         self.repo.get(-1)
            
            
    # def testGetUnitRecordIds(self):
    #     # Check that valid list of ids are returned
    #     test_ret = [1, 3]
    #     result = self.repo.get_unit_record_ids("1111", False)
    #     self.assertListEqual(test_ret, result)
        
    #     # Check that valid most recent id returned
    #     result = self.repo.get_unit_record_ids("1111", True)
    #     self.assertEqual(3, result)
        
    #     # Test that an exception is raised when nothing is found
    #     with self.assertRaises(RepositoryNotFoundError):
    #         result = self.repo.get_unit_record_ids("unit", True)
            
            
    # def testGetRecentTrains(self):
    #     # Test successful retrieval of new record
    #     results = self.repo.get_recent_trains("1111", 1)
    #     expected = [self.test_data[2]]
    #     self.assertListEqual(expected, results)
        
    #     # Test failed retrieval of records
    #     results = self.repo.get_recent_trains("bruh", 1)
    #     self.assertListEqual([], results)

            
    # def testAddNewPin(self):
    #     # Test successful pin update
    #     result_id = self.repo.add_new_pin(4, "1111")
    #     self.assertListEqual([3], result_id)
        
    #     result_id = self.repo.add_new_pin(3, "1111")
    #     self.assertListEqual([], result_id)
            
            
    # ######################################
    # ##  get_record_column_by_unit_addr  ##
    # ###################################### 
    # def _run_get_record_case(self, unit_addr, column, position, recent, expected):
    #     result = self.repo.get_record_column_by_unit_addr(unit_addr, column, position, recent)
    #     self.assertIsInstance(result, type(expected))
    #     self.assertEqual(expected, result)
          
    # def testGetRecordSymbol(self):
    #     test_cases = [
    #         # Below are the tests for symbol_id
    #         ("2222", "symbol_id", True, [2]),
    #         ("2222", "symbol_id", False, [2]),
    #         ("2222", "symbol_id", None, [2, 2]), 
    #         # Below are the tests for engine_num
    #         ("1111", "engine_num", True, [1]),
    #         ("1111", "engine_num", False, [1]),
    #         ("1111", "engine_num", None, [1, 1]), 
    #         # Below are the not found cases
    #         ("0000", "engine_num", True, []),
    #         ("0000", "engine_num", False, []),
    #         ("0000", "engine_num", None, [])
    #     ]
        
    #     for unit, col, rec, exp in test_cases:
    #         # If this fails, the error message will include these params
    #         with self.subTest(unit=unit, col=col, rec=rec, exp=exp):
    #             result = self.repo.get_record_column_by_unit_addr(unit, col, rec)
    #             self.assertEqual(exp, result)
            
    #     # Make sure exception raised if not valid column
    #     with self.assertRaises(RepositoryInvalidArgumentError):
    #         self.repo.get_record_column_by_unit_addr("5545", "Bob")
            
    #     with self.assertRaises(RepositoryParsingError):
    #         self.repo.get_record_column_by_unit_addr("1111", "engine_num", "Bob")
        
    
    # # ############################
    # # ##  update_signal_values  ##
    # # ############################
    # def testUpdateSignalValues(self):
    #     test_symbol = None
    #     test_engine = None
        
    #     # Test no values change
    #     result = self.repo.update_signal_values(1, test_symbol, test_engine)
    #     self.assertEqual(None, result)
        
    #     test_cases = [
    #         (2, None),
    #         (None, 2),
    #         (1, 1)
    #     ]
        
    #     for sym, eng in test_cases:
    #         with self.subTest(sym=sym, eng=eng):
    #             updated = self.repo.update_signal_values(1, sym, eng, False)
    #             self.session.add(updated)
    #             self.session.flush()
                
    #             result = self.repo.get(1, False)
    #             self.assertEqual(updated, result)

    
    # ###########################
    # ##  get_station_records  ##
    # ###########################
    # def testGetStationRecords(self):
    #     self.maxDiff = None
    #     # All tests will be executed with recent=False in this class
    #     expected = [self.test_data[0], self.test_data[2]]
    #     result = self.repo.get_station_records(1)
    #     self.assertListEqual(expected, result)
        
    #     with patch.object(Session, "execute") as mock:
    #         mock.side_effect = SQLAlchemyError
    #         with self.assertRaises(RepositoryInternalError):
    #             self.repo.get_station_records(1)
        
        
    # #####################
    # ##  verify_record  ##
    # #####################
    # def testVerifyRecord(self):
    #     sym, loc = 2, "RG00"
        
    #     # Get the updated instance in session
    #     updated = self.repo.verify_record(3, sym, loc, False)
    #     self.session.add(updated)
    #     self.session.flush()
        
    #     # Make sure the changes are correctly reflected in the session
    #     result = self.repo.get(3, False)
    #     self.assertEqual(updated, result)
        
    #     with patch.object(RecordRepository, "update_with_pk") as mock:
    #         mock.side_effect = SQLAlchemyError
    #         with self.assertRaises(RepositoryInternalError):
    #             self.repo.verify_record(3, sym, loc)
        
        
    # ################################
    # ##  get_records_in_timeframe  ##
    # ################################
    # def testGetRecordsInTimeframe(self):
    #     self.maxDiff = None
    #     expected = [
    #         {
    #             'id': 4, 
    #             'date_rec': self.test_data[3].date_rec, 
    #             'unit_addr': '2222', 
    #             'station_name': 'test station2',
    #             'symb_name': 'Test Symbol2', 
    #             'engine_num': 2, 
    #             'locomotive_num': 'CY00',
    #             'Data_type': 'TRAIN'
    #         },
    #         {
    #             'id': 3, 
    #             'date_rec': self.test_data[2].date_rec, 
    #             'unit_addr': '1111', 
    #             'station_name': 'test station1',
    #             'symb_name': 'Test Symbol1', 
    #             'engine_num': 1, 
    #             'locomotive_num': 'EL00',
    #             'Data_type': 'TRAIN'
    #         },
    #         {
    #             'id': 2,
    #             'date_rec': self.test_data[1].date_rec,
    #             'unit_addr': '2222', 
    #             'station_name': 'test station2',
    #             'symb_name': 'Test Symbol2', 
    #             'engine_num': 2, 
    #             'locomotive_num': 'TG00',
    #             'Data_type': 'TRAIN'
    #         },
    #         {
    #             'id': 1,
    #             'date_rec': self.test_data[0].date_rec,
    #             'unit_addr': '1111', 
    #             'station_name': 'test station1',
    #             'symb_name': 'Test Symbol1', 
    #             'engine_num': 1, 
    #             'locomotive_num': 'CT00',
    #             'Data_type': 'TRAIN'
    #         }
    #     ]
    #     dt = datetime.strptime("1998-01-08 04:05:06", "%Y-%m-%d %H:%M:%S")
    #     results = self.repo.get_records_in_timeframe(-1, dt, False)
    #     self.assertListEqual(expected[2:], results)
        
    #     results = self.repo.get_records_in_timeframe(1, dt, False)
    #     self.assertListEqual([expected[3]], results)
        
    #     results = self.repo.get_records_in_timeframe(-1, dt, True)
    #     self.assertListEqual(expected[:2], results)
        
    #     results = self.repo.get_records_in_timeframe(1, dt, True)
    #     self.assertListEqual([expected[1]], results)
        
    #     results = self.repo.get_records_in_timeframe(1, dt)
    #     self.assertListEqual(expected[1::2], results)
        
    #     with patch.object(Session, "execute") as mock:
    #         mock.side_effect = SQLAlchemyError
    #         with self.assertRaises(RepositoryInternalError):
    #             self.repo.get_records_in_timeframe(-1, dt, True)
                
                
    #################################
    ##  TESTS FOR BASE REPOSITORY  ##
    #################################
    
    def testRepositoryPkeyInspect(self):    
        # Test that the primary key of the repository is correct
        self.assertEqual("id", self.repo.pkey)
        
        # Test that the primary key of the repository is None when model is not specified
        self.repo = BaseRepository(None, self.session)
        self.assertEqual(None, self.repo.pkey)
        
        # Test inspection error on invalid instance
        self.repo = BaseRepository(int, self.session)
        self.assertEqual(None, self.repo.pkey)
        
        # Test if inspection doesn't find primary key
        with patch('backend.src.db.db_core.repository.inspect') as mock_inspect:
            mock_inspect.return_value.primary_key = []
            self.repo = BaseRepository(TestTrainRecord, self.session)
            self.assertEqual(None, self.repo.pkey)
        
    def testRepositoryGet(self):
        # Test that the dictionary returned is equal
        expected = self.test_data[0]
        result = self.repo.get(1)
        self.assertDictEqual(expected._asdict(), result)
        
        # Test that the ORM returned is equal
        result = self.repo.get(1, False)
        self.assertEqual(expected, result)
        
        # Test that an exception is raised when a row cannot be found
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.get(100)
            
    def testRepositoryUpdate(self):
        # Test that empty update list returns nothing
        result = self.repo.update([])
        self.assertEqual([], result)
        
        # Test that a single update works correctly
        updated_data = {'id': 1, 'date_rec': datetime.now(), 'unit_addr': '9999'}
        result = self.repo.update([(self.test_data[0], updated_data)])
        result_session = self.repo.get(1)
        
        self.assertEqual(updated_data['date_rec'], result[0]['date_rec'])
        self.assertEqual(updated_data['unit_addr'], result[0]['unit_addr'])
        
        self.assertEqual(updated_data['date_rec'], result_session['date_rec'])
        self.assertEqual(updated_data['unit_addr'], result_session['unit_addr'])
        
        # Test that multiple updates work correctly
        update_payload = [(self.test_data[1], updated_data), (self.test_data[2], updated_data)]
        result = self.repo.update(update_payload)
        self.assertEqual(2, len(result))
        
        for i in range(2, 4):
            self.assertEqual(updated_data['date_rec'], result[i - 2]['date_rec'])
            self.assertEqual(updated_data['unit_addr'], result[i - 2]['unit_addr'])
            
            result_session = self.repo.get(i)
            self.assertEqual(updated_data['date_rec'], result_session['date_rec'])
            self.assertEqual(updated_data['unit_addr'], result_session['unit_addr'])
            
        # Test that unchanged updates returns empty result
        unchanged_data = {'id': 1, 'unit_addr': self.test_data[3].unit_addr}
        result = self.repo.update([(self.test_data[3], unchanged_data)])
        self.assertEqual([], result)


    def testRepositoryUpdateErrors(self):
        # Test that an object key of an incorrect type raises InvalidArgumentError
        with self.assertRaises(RepositoryInvalidArgumentError):
            self.repo.update([(1, {'unit_addr': '9999'})])
            
        # Test exception is raised if TypeError is raised
        with self.assertRaises(RepositoryParsingError):
            self.repo.update({self.test_data[0]: {'unit_addr': '9999'}})
            
        # Test exception is raised if field to update is not in ORM
        with self.assertRaises(RepositoryInvalidArgumentError):
            self.repo.update([(self.test_data[0], {'boom': 'bap'})])
            
    
    def testUpdateWithPrimaryKey(self):
        # Test that updating with a primary key is functional, assuming that update tests are correct
        updated_data = {'locomotive_num': "JBL", 'unit_addr': '9999'}
        result = self.repo.update_with_pk(1, updated_data)
        result_session = self.repo.get(1)
        
        self.assertEqual(updated_data['locomotive_num'], result['locomotive_num'])
        self.assertEqual(updated_data['unit_addr'], result['unit_addr'])
        
        self.assertEqual(updated_data['locomotive_num'], result_session['locomotive_num'])
        self.assertEqual(updated_data['unit_addr'], result_session['unit_addr'])
        
        # Test that if get fails to find the object, an exception is raised
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.update_with_pk(100, updated_data)
            
        # Test that if no changes are made, then None is returned
        updated_data = {'locomotive_num': self.test_data[1].locomotive_num, 'unit_addr': self.test_data[1].unit_addr}
        result = self.repo.update_with_pk(2, updated_data)
        self.assertIsNone(result)


    def testRepositoryCreate(self):
        pass
            
    


if __name__ == "__main__":
    unittest.main()
            
        