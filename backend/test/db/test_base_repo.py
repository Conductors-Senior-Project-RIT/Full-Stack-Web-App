from datetime import datetime
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import IntegrityError, ProgrammingError
import unittest

from sqlalchemy import text

from backend.database import db
from backend.src.db.db_core.exceptions import RepositoryInvalidArgumentError, RepositoryNotFoundError, RepositoryParsingError
from backend.src.db.db_core.repository import BaseRepository
from backend.test.base_test_case import BaseTestCase
from backend.test.db.test_utils import TestRepository, TestRepository, TestTrainRecord, return_test_data


class TestBaseRepository(BaseTestCase):  
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
        print("Jigglebutt")
        print([r.id for r in self.test_data])
        
    
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
        # Test that a single record is created successfully
        date_rec = datetime.now()
        station_rec = 1
        new_record_data = {"date_rec": date_rec, "station_recorded": station_rec}
            
        result = self.repo.create(new_record_data)[0]
        self.assertEqual(5, result["id"])
        result_session = self.repo.get(result["id"])
        
        self.assertEqual(date_rec, result["date_rec"])
        self.assertEqual(station_rec, result["station_recorded"])
        self.assertEqual(date_rec, result_session["date_rec"])
        self.assertEqual(station_rec, result_session["station_recorded"])
        
        # Test that multiple records are created successfully
        result = self.repo.create([new_record_data, new_record_data])
        self.assertEqual(2, len(result))
        
        for i in range(6, 8):
            result_session = self.repo.get(i)
            
            self.assertEqual(date_rec, result[i - 6]["date_rec"])
            self.assertEqual(station_rec, result[i - 6]["station_recorded"])
            self.assertEqual(date_rec, result_session["date_rec"])
            self.assertEqual(station_rec, result_session["station_recorded"])
        
        # Test no results returned when new_data is empty
        result = self.repo.create([])
        self.assertEqual([], result)
        
        # Test that ModelType is returned when to_dict is False
        result = self.repo.create(new_record_data, to_dict=False)[0]
        self.assertIsInstance(result, TestTrainRecord)
        self.assertEqual(8, result.id)
        
    def testRepositoryCreateErrors(self):
        # Create some arbitrary record to test primary key collision
        date_rec = datetime.now()
        station_rec = 1
        new_record_data = {"id": 999, "date_rec": date_rec, "station_recorded": station_rec}
        
        self.repo.create(new_record_data, False)[0]
        self.repo.session.flush()
        
        # Test that if a primary key collision occurs, then error is raised
        with self.assertRaises(RepositoryParsingError) as exc:
            sp = self.repo.session.begin_nested()
            self.repo.create({"id": 999, "date_rec": datetime.now(), "station_recorded": 2}, False) 
        # The exception should contain the root cause (IntegrityError) if primary key collision occurs
        # Rollback the changes in order to test that original record is intact
        sp.rollback()
        e = exc.exception            
        self.assertIsInstance(e.__cause__(), IntegrityError)
        
        # Test that the original record still has the same column values after failed creation
        instance = self.repo.get(999, False)
        self.assertEqual(date_rec, instance.date_rec)
        self.assertEqual(station_rec, instance.station_recorded)
            
        # Test that a parsing error is raised when the input data is not a dict or list of dicts
        with self.assertRaises(RepositoryParsingError) as exc:
            self.repo.create(["not a dict"])
        # The exception should contain the root cause (TypeError)
        e = exc.exception            
        self.assertIsInstance(e.__cause__(), TypeError)
            
        # Test that a parsing error is raised when the input data dict is has incompatible types for the model
        with self.assertRaises(RepositoryParsingError) as exc:
            sp = self.session.begin_nested()
            self.repo.create([{"date_rec": Exception, "station_recorded": station_rec}])
        # The exception should contain the root cause (ProgrammingError)
        sp.rollback()
        e = exc.exception            
        self.assertIsInstance(e.__cause__(), ProgrammingError)
        
        # Test that a parsing error is raised when null constraint is violated
        with self.assertRaises(RepositoryParsingError) as exc:
            sp = self.session.begin_nested()
            self.repo.create([{"station_recorded": station_rec}])
        # The exception should contain the root cause (IntegrityError)
        sp.rollback()
        e = exc.exception            
        self.assertIsInstance(e.__cause__(), IntegrityError)
        
    
    def testRepositoryDelete(self):
        # Test that deleting a record with an ORM instance works correctly
        self.repo.delete(self.test_data[0])
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.get(1)
            
        # Test that deleting a record with a primary key value works correctly
        self.repo.delete(2)
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.get(2)
            
        # Test that trying to delete a non-existent record raises an exception
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.delete(100)
            
    
    def testObjsToDicts(self):
        # Test that a list of dicts is returned when given a list of ORM objects
        result = self.repo.objs_to_dicts(self.test_data)
        for i in range(len(self.test_data)):
            self.assertDictEqual(self.test_data[i]._asdict(), result[i])
            
        # Test that a single dict is returned when given a single ORM object
        result = self.repo.objs_to_dicts(self.test_data[0])
        self.assertDictEqual(self.test_data[0]._asdict(), result)
        
        # Test that when an iterable of convertible objects is given, a list of dicts is returned
        result = self.repo.objs_to_dicts([[test] for test in self.test_data])
        expected = [test._asdict() for test in self.test_data]
        self.assertListEqual(expected, result)
        
        # Test when instances containing "_mapping" are passed, they are converted correctly
        test_data = {"id": 1, "date_rec": datetime.now()}
        class MappingStub:
            _mapping = test_data
        
        result = self.repo.objs_to_dicts(MappingStub())
        self.assertEqual(test_data, result)
        
        # Test when instances that don't contain "_asdict__" or "_mapping" are passed, 
        # but are still dict-like (contain keys() and __getitem__), they are converted correctly
        class ConvertibleStub:
            def keys(self):
                return ["id", "station_recorded"]
            def __getitem__(self, key):
                return {"id": 1, "station_recorded": 1}[key]
        result = self.repo.objs_to_dicts(ConvertibleStub())
        self.assertEqual({"id": 1, "station_recorded": 1}, result)
        
        # Test that invalid types raise an exception
        with self.assertRaises(RepositoryParsingError):
            self.repo.objs_to_dicts(123)  

        # Test conversion to string works correctly
        result = self.repo.objs_to_dicts(self.test_data[0], convert_to_string={"date_rec"})
        self.assertEqual(str(self.test_data[0].date_rec), result["date_rec"])
        
        # Test that an empty list is returned when given an empty list
        result = self.repo.objs_to_dicts([])
        self.assertEqual([], result)
        
    
if __name__ == "__main__":
    unittest.main()
            