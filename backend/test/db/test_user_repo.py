# from datetime import time
# import unittest

# from backend.database import db
# from backend.src.db.db_core.models import User
# from backend.src.db.user_repo import UserRepository
# from backend.test.base_test_case import BaseTestCase

# class TestUserRepository(BaseTestCase):
#     def setUp(self):
#         """
#         Creating a fake User so certain attributes are easier to test (like getting the right user id)
#         """
#         self.session = db.session
#         self.repo = UserRepository(db.session) 
#         self.test_user = User(id=67,
#                               email="faker@gmail.com",
#                               passwd="hashed_passw123",
#                               token="34we56rt7y8u9iou8biyexew8irxyiew",
#                               acc_status=2, #normal user
#                               starting_time=time(8, 0),
#                               ending_time=time(16, 0),
#                               pushover_id=None, # doesn't matter cuz we not gona use pushover lol
#                               ) # transient/ 'initial' state
#         self.session.add(self.test_user) # transient -> pending state (flush() to emit sql command to db)
#         self.session.flush() # pending -> persistent (but transaction still opened swag, session will close/ release resources after last test method runs for this test suite)

#     def tearDown(self):
#         db.session.rollback() # persistent -> state revert changes made from every test_method ran

#     ###########################
#     ##  create_new_user  ##
#     ###########################
#     def test_create_new_user(self):
#         """
#         TODO: add error handling decorators to user_repo and test it here (?, or should separate tests for excpetions be sufficient hmmm)

#         """

#         # if everything goes well
#         user_id = self.repo.create_new_user("newtestemail@gmail.com", "hashed_pw")
#         self.assertIsInstance(user_id, int)
#         self.assertGreater(user_id, 0) # serial pk start at 1

#         # supplementary functions relating to user/new users like get_id() to verify functionality

#         pass

#         # if things go wrong/ exceptions that can happen

#         pass


#     def test_get_user_id(self):
#         email = "newtestemail@gmail.com"
#         actual = self.repo.get_user_id(email)
#         expected = 1
#         self.assertEqual(actual, expected)

# if __name__ == '__main__':
#     unittest.main()