import unittest

from backend.database import db
from backend.src.db.record_types import (
    RecordFactory,
    RecordTypes,
    HOTRecord,
    HOTCollation,
    EOTRecord,
    EOTCollation,
)
from backend.src.db.db_core.exceptions import RepositoryRecordInvalid
from backend.test.base_test_case import BaseTestCase


class TestRecordTypes(BaseTestCase):
    def setUp(self):
        self.factory = RecordFactory()
    
    def tearDown(self):
        db.session.rollback()  # revert changes made from every test_method ran
        db.session.close()

    def test_get_repository(self):
        session = db.session

        # Test invalid cases
        cases = ["1", 0, 4]
        for case in cases:
            with self.assertRaises(RepositoryRecordInvalid):
                self.factory.get_record_repository(session, case)

        # Test valid EOT cases
        eot_int = self.factory.get_record_repository(session, 1)
        self.assertIs(eot_int.model, EOTRecord)
        self.assertIs(eot_int.collation, EOTCollation)

        eot_enum = self.factory.get_record_repository(session, RecordTypes.EOT)
        self.assertIs(eot_enum.model, EOTRecord)
        self.assertIs(eot_enum.collation, EOTCollation)

        # Test valid HOT cases
        hot_int = self.factory.get_record_repository(session, 2)
        self.assertIs(hot_int.model, HOTRecord)
        self.assertIs(hot_int.collation, HOTCollation)

        hot_enum = self.factory.get_record_repository(session, RecordTypes.HOT)
        self.assertIs(hot_enum.model, HOTRecord)
        self.assertIs(hot_enum.collation, HOTCollation)

        # TODO: Test valid DPU cases

    def test_get_all_repositories(self):
        session = db.session

        models = [(EOTRecord, EOTCollation), (HOTRecord, HOTCollation)]
        results = self.factory.get_all_repositories(session)

        for result, expected in zip(results, models):
            self.assertIs(result.model, expected[0])
            self.assertIs(result.collation, expected[1])


if __name__ == "__main__":
    unittest.main()
