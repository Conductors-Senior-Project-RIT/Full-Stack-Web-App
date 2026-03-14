import unittest

from backend.db import db
from backend.src.db.record_types import *
from backend.test.base_test_case import BaseTestCase

class TestRecordTypes(BaseTestCase):
    def tearDown(self):
        db.session.rollback() # revert changes made from every test_method ran
        db.session.close()

    def test_get_repository(self):
        session = db.session
        
        # Test invalid cases
        cases = ["1", 0, 4]
        for case in cases:
            with self.assertRaises(RepositoryRecordInvalid):
                get_record_repository(session, case)
        
        # Test valid EOT cases
        eot_int = get_record_repository(session, 1)
        self.assertIsInstance(eot_int, EOTRepository)
        
        eot_enum = get_record_repository(session, RecordTypes.EOT)
        self.assertIsInstance(eot_enum, EOTRepository)
        
        # Test valid HOT cases
        hot_int = get_record_repository(session, 2)
        self.assertIsInstance(hot_int, HOTRepository)
        
        hot_enum = get_record_repository(session, RecordTypes.HOT)
        self.assertIsInstance(hot_enum, HOTRepository)
        
        # Test valid DPU cases
        dpu_int = get_record_repository(session, 3)
        self.assertIsInstance(dpu_int, DPURepository)
        
        dpu_enum = get_record_repository(session, RecordTypes.DPU)
        self.assertIsInstance(dpu_enum, DPURepository)
        
        self.tearDown()
    
    def test_get_all_repositories(self):
        session = db.session
        
        repos = [EOTRepository, HOTRepository, DPURepository]    
        results = get_all_repositories(session)
    
        for result, expected in zip(results, repos):
            self.assertIsInstance(result, expected)
            
        self.tearDown()
        
    def test_has_values(self):
        # Test valid case
        self.assertTrue(has_value(1))
        
        # Test invalid cases
        self.assertFalse(has_value(4))
        self.assertFalse(has_value("4"))

    
if __name__ == '__main__':
    unittest.main()