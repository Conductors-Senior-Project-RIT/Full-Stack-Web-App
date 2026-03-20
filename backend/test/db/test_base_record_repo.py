from datetime import datetime
from itertools import product
from typing import Any
import unittest
from unittest.mock import patch
from collections import namedtuple

from sqlalchemy import Boolean, Column, Integer, String, select
from sqlalchemy.orm import mapped_column
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import TIMESTAMP


from mock_alchemy.mocking import UnifiedAlchemyMagicMock

from backend.database import Base, db
from backend.src.db.base_record_repo import RecordRepository
from backend.src.db.database_core import RepositoryInternalError, RepositoryInvalidArgumentError, RepositoryNotFoundError
from backend.test.base_test_case import BaseTestCase


class TestRecord(Base):
    __tablename__ = "testrecords"
    id = Column(Integer, primary_key=True, nullable=False)
    date_rec = Column(TIMESTAMP(timezone=True), nullable=False)
    station_recorded = Column(Integer)
    most_recent = Column(Boolean, default=True)
    unit_addr = Column(String(240), default="unknown")
    symbol_id = Column(Integer, default=None)
    engine_num = Column(Integer, default=None)


class TestRepository(RecordRepository):  
    def __init__(self, session):
        super().__init__(session, TestRecord, "TestRecords", "Test Record", "test")
      
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


TestRow = namedtuple(
    "TestRow", 
    ["id", "station_recorded", "most_recent", "unit_addr", "symbol_id", "engine_num"]
)

def create_test_row(
    id: int, 
    station_recorded: int,
    most_recent=True, 
    unit_addr="unknown", 
    symbol_id: int | None = None, 
    engine_num: int | None = None
) -> TestRow:
    return TestRow(
        id=id,
        station_recorded=station_recorded,
        most_recent=most_recent,
        unit_addr=unit_addr,
        symbol_id=symbol_id,
        engine_num=engine_num
    )


class TestRecordRepository(BaseTestCase):
    """We don't need to use BaseTestCase since this class does not use DB connection."""
    def setUp(self):
        self.session = db.session
        self.repo = TestRepository(self.session)
        TestRecord.__table__.drop(bind=db.engine, checkfirst=True)
        TestRecord.__table__.create(bind=db.engine, checkfirst=True)
        
        self.test_data = [
            TestRecord(
                date_rec=datetime.strptime("1999-01-08 04:05:06", "%Y-%m-%d %H:%M:%S"),
                station_recorded=1,
                most_recent=False,
                unit_addr="1111",
                symbol_id=7,
                engine_num=1,
            ),
            TestRecord(
                date_rec=datetime.strptime("2003-02-05 06:53:08", "%Y-%m-%d %H:%M:%S"),
                station_recorded=1,
                most_recent=False,
                unit_addr="2222",
                symbol_id=8,
                engine_num=2
            ),
            TestRecord(
                date_rec=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                station_recorded=1,
                most_recent=True,
                unit_addr="1111",
                symbol_id=9,
                engine_num=3
            ),
            TestRecord(
                date_rec=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                station_recorded=1,
                most_recent=True,
                unit_addr="2222",
                symbol_id=10,
                engine_num=4
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
        self.assertEqual("Test Record", self.repo.get_record_name())
        self.assertEqual("test", self.repo.get_record_identifier())
    
    
    def testGetTrainRecordLogic(self):
        # Test that successful retrieval
        result = self.repo.get_train_record(1)
        self.assertDictEqual(self.test_data[0]._asdict(), result)
        
        # Test invalid id
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.get_train_record(-1)
            
        # Test invalid argument
        with self.assertRaises(RepositoryInvalidArgumentError):
            self.repo.get_train_record("1")
            
            
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
        self.assertListEqual([self.test_data[2]], results)
        
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
            ("2222", "symbol_id", True, [10]),
            ("2222", "symbol_id", False, [8]),
            ("2222", "symbol_id", None, [8, 10]), 
            # Below are the tests for engine_num
            ("1111", "engine_num", True, [3]),
            ("1111", "engine_num", False, [1]),
            ("1111", "engine_num", None, [1, 3]), 
            # Below are the not found cases
            ("0000", "engine_num", True, []),
            ("0000", "engine_num", False, []),
            ("0000", "engine_num", None, [])
        ]
        
        for unit, col, pos, rec, exp in test_cases:
            # If this fails, the error message will include these params
            with self.subTest(unit=unit, col=col, pos=pos, rec=rec, exp=exp):
                result = self.repo.get_record_column_by_unit_addr(unit, col, rec)
                self.assertEqual(exp, result)
            
        # Make sure exception raised if not valid column
        with self.assertRaises(RepositoryInvalidArgumentError):
            self.repo.get_record_column_by_unit_addr("5545", "Bob", "first")
            
        with self.assertRaises(RepositoryInvalidArgumentError):
            self.repo.get_record_column_by_unit_addr("1111", "engine_num", "Bob")
        
    
    # #################################
    # ##  update_record_field_by_id  ##
    # #################################
    # def testUpdateRecordField(self):
        
        
        
            
if __name__ == "__main__":
    unittest.main()
            
        