from datetime import datetime
import unittest

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.dialects.postgresql import TIMESTAMP

from backend.database import Base, db
from backend.src.db.base_record_repo import RecordRepository
from backend.src.db.database_core import RepositoryInvalidArgumentError, RepositoryNotFoundError, RepositoryParsingError
from backend.test.base_test_case import BaseTestCase


class TestTrainRecord(Base):
    __tablename__ = "trainrecords"
    id = Column(Integer, primary_key=True, nullable=False)
    date_rec = Column(TIMESTAMP(timezone=True), nullable=False)
    station_recorded = Column(Integer, nullable=False)
    most_recent = Column(Boolean, default=True)
    unit_addr = Column(String(240), default="unknown", nullable=False)
    symbol_id = Column(Integer, default=None)
    engine_num = Column(Integer, default=None)
    locomotive_num = Column(String(240), default="unknown", nullable=False)
    verified = Column(Boolean, default=False, nullable=False)


class TestRepository(RecordRepository):  
    model = TestTrainRecord
    
    def __init__(self, session):
        super().__init__(session, "Train Record", "train")
      
    def get_train_history(self, id, page, num_results):
        pass

    def create_train_record(self, args, datetime_string):
        pass

    def get_recent_station_records(self, station_id):
        pass

    def parse_station_records(self, station_records):
        pass

    def get_record_collation(self, page):
        pass

    def get_records_by_verification(self, page, verified):
        pass


class TestRecordRepository(BaseTestCase):
    """We don't need to use BaseTestCase since this class does not use DB connection."""
    def setUp(self):
        self.session = db.session
        self.repo = TestRepository(self.session)
        TestTrainRecord.__table__.drop(bind=db.engine, checkfirst=True)
        TestTrainRecord.__table__.create(bind=db.engine, checkfirst=True)
        
        self.test_data = [
            TestTrainRecord(
                id=1,
                date_rec=datetime.strptime("1999-01-08 04:05:06", "%Y-%m-%d %H:%M:%S"),
                station_recorded=0,
                most_recent=False,
                unit_addr="1111",
                symbol_id=1,
                engine_num=1,
                locomotive_num="CT00",
                verified=True
            ),
            TestTrainRecord(
                id=2,
                date_rec=datetime.strptime("2003-02-05 06:53:08", "%Y-%m-%d %H:%M:%S"),
                station_recorded=1,
                most_recent=False,
                unit_addr="2222",
                symbol_id=1,
                engine_num=2,
                locomotive_num="TG00",
                verified=True
            ),
            TestTrainRecord(
                id=3,
                date_rec=datetime.now(),
                station_recorded=0,
                most_recent=True,
                unit_addr="1111",
                symbol_id=0,
                engine_num=3,
                locomotive_num="EL00",
                verified=False
            ),
            TestTrainRecord(
                id=4,
                date_rec=datetime.now(),
                station_recorded=1,
                most_recent=True,
                unit_addr="2222",
                symbol_id=0,
                engine_num=4,
                locomotive_num="CY00",
                verified=False
            )
        ]
        
        self.session.add_all(self.test_data)
        
        
    def tearDown(self):
        self.session.rollback() # revert changes made from every test_method ran
        self.session.close()
        
        
    ###############
    ##  Getters  ##
    ###############
    def testGetters(self):
        self.assertEqual("Train Record", self.repo.get_record_name())
        self.assertEqual("train", self.repo.get_record_identifier())
    
    
    def testGetTrainRecordLogic(self):
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
        results = self.repo.get_recent_trains("2222", 1)
        expected = [self.test_data[3]]
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
            ("2222", "symbol_id", True, [0]),
            ("2222", "symbol_id", False, [1]),
            ("2222", "symbol_id", None, [1, 0]), 
            # Below are the tests for engine_num
            ("1111", "engine_num", True, [3]),
            ("1111", "engine_num", False, [1]),
            ("1111", "engine_num", None, [1, 3]), 
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
        expected = self.test_data[0].copy()
        
        # Test no values change
        result = self.repo.update_signal_values(1, test_symbol, test_engine)
        self.assertListEqual([], result)
        
        test_cases = [
            (99, None),
            (None, 99),
            (100, 100)
        ]
        
        for sym, eng in test_cases:
            with self.subTest(sym=sym, eng=eng):
                if sym:
                    expected.symbol_id = sym
                if eng:
                    expected.engine_num = eng
                
                result = self.repo.update_signal_values(1, sym, eng)
                self.assertEqual(expected._asdict(), result)

    
    ###########################
    ##  get_station_records  ##
    ###########################
    def testGetStationRecords(self):
        # All tests will be executed with recent=False in this class
        expected = [self.test_data[1], self.test_data[3]]
        result = self.repo.get_station_records(1)
        self.assertListEqual(expected, result)
        
        
    #####################
    ##  verify_record  ##
    #####################
    def testVerifyRecord(self):
        expected = self.test_data[2].copy()
        sym, loc = 500, "RG00"
        
        expected.symbol_id = sym
        expected.locomotive_num = loc
        expected.verified = True
        
        self.repo.verify_record(3, sym, loc)
        
        result = self.repo.get(3, False)
        self.assertEqual(expected, result)
        
    ################################
    ##  get_records_in_timeframe  ##
    ################################
    def testGetRecordsInTimeframe(self):
        pass
    
        
        
            
if __name__ == "__main__":
    unittest.main()
            
        