import unittest

from backend.database import db
from backend.src.db.user_repo import UserRepository
from backend.test.base_test_case import BaseTestCase

class TestUserRepository(BaseTestCase):

    def tearDown(self):
        db.session.rollback() # revert changes made from every test_method ran

    def test_get_user_id(self):
        user = UserRepository(db.session)
        actual = user.get_user_id('test@test.test')
        expected = 0
        self.assertEqual(actual, expected)

if __name__ == '__main__':
    unittest.main()