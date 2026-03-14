from unittest.mock import patch
from collections import namedtuple

from sqlalchemy.orm.scoping import scoped_session

from backend.db import db
from backend.src.db.base_record_repo import RecordRepository
from backend.src.db.database_core import RepositoryInvalidArgumentError, RepositoryNotFoundError
from backend.test.base_test_case import BaseTestCase


class TestRepository(RecordRepository):
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


TestRow = namedtuple("RecordRow", ["id", "most_recent"])


class TestRecordRepository(BaseTestCase):
    def setUp(self):
        super().setUpClass()
        self.session = db.session
        self.repo = TestRepository(
            self.session, "testTable", "testName", "testIdent"
        )
        
    def tearDown(self):
        self.session.rollback() # revert changes made from every test_method ran
        self.session.close()
        
        
    ###############
    ##  Getters  ##
    ###############
    def testGetters(self):
        self.assertEqual("testName", self.repo.get_record_name())
        self.assertEqual("testIdent", self.repo.get_record_identifier())
        
    
    def testGetTrainRecordLogic(self):
        # Check that it returns correct parsed dictionary
        with patch.object(RecordRepository, "session", create=True) as mock_session:
            mock_session.execute.return_value.one_or_none.return_value = TestRow(id=1, most_recent=True)
            self.repo.session = mock_session
            
            result = self.repo.get_train_record(1)
            self.assertDictEqual({"id": 1, "most_recent": True}, result)
            
            # Check that it raises exception when no record found
            with self.assertRaises(RepositoryNotFoundError):
                mock_session.execute.return_value.one_or_none.return_value = None
                
                result = self.repo.get_train_record(-1)
                self.assertIsNone(result)
                
        # Check that it raises exception for invalid arg types
        with self.assertRaises(RepositoryInvalidArgumentError):
            self.repo.get_train_record("1")
            
    def testGetUnitRecordIds(self):
        with patch.object(RecordRepository, "session", create=True) as mock_session:
            # Check that it returns the correct id when most_recent = True
            test_ret = [1, 2, 3]
            mock_session.execute.return_value.scalars.return_value.all.return_value = test_ret
            self.repo.session = mock_session
            
            result = self.repo.get_unit_record_ids("unit", True)
            self.assertEqual(3, result)
            
            # Check that returns all ids when most_recent = False
            result = self.repo.get_unit_record_ids("unit", False)
            self.assertEqual(test_ret, result)
            
            # Test that an exception is raised when nothing is found
            with self.assertRaises(RepositoryNotFoundError):
                mock_session.execute.return_value.scalars.return_value.all.return_value = []
                result = self.repo.get_unit_record_ids("unit", True)
                self.assertIsNone(result)
            
    def testGetRecentTrains(self):
        with patch.object(RecordRepository, "session", create=True) as mock_session:
            # Test that it correctly returns list of dicts
            test_rows = [TestRow(id=1, most_recent=False), TestRow(id=2, most_recent=True)]
            mock_session.execute.return_value.all.return_value = test_rows
            self.repo.session = mock_session
            
            expected = [{"id": 1, "most_recent": False}, {"id": 2, "most_recent": True}]
            result = self.repo.get_recent_trains("test", "test")
            self.assertListEqual(expected, result)
            
    # Probably can just test with child classes
    def testAddNewPin(self):
        with patch.object(RecordRepository, "session", create=True) as mock_session:
            # Test that it correctly returns one ID
            mock_session.execute.return_value.scalars.return_value.all.return_value = [2, 3]
            self.repo.session = mock_session
            result = self.repo.add_new_pin(1, 1337)
            self.assertListEqual([2, 3], result)
            
            # Test that it returns empty list if no updates made
            mock_session.execute.return_value.scalar.return_value = []
            self.repo.add_new_pin(-1, 7331)
            