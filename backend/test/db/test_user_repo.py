from datetime import time
import unittest

from backend.database import db
from backend.src.db.db_core.exceptions import RepositoryInternalError, RepositoryNotFoundError
from backend.src.db.db_core.models import User
from backend.src.db.user_repo import UserRepository
from backend.test.base_test_case import BaseTestCase

class TestUserRepository(BaseTestCase): # testing user model
    def setUp(self):
        """
        Creating a fake User so certain attributes are easier to test (like getting the right user id)
        """
        self.repo = UserRepository(db.session) 
        self.test_user = User(id=67,
                              email="faker@gmail.com",
                              passwd="hashed_passw123",
                              token="34we56rt7y8u9iou8biyexew8irxyiew",
                              acc_status=2, #normal user
                              starting_time=time(8, 0),
                              ending_time=time(16, 0),
                              pushover_id=None, # doesn't matter cuz we not gona use pushover lol
                              ) # transient/ 'initial' state
        db.session.add(self.test_user) # transient -> pending state (flush() to emit sql command to db)
        db.session.flush() # pending -> persistent (but transaction still opened swag, session will close/ release resources after last test method runs for this test suite)

        self.new_fake_email = "newtestemail@gmail.com"
        self.new_fake_password = "hashed_pw"

    def tearDown(self):
        db.session.rollback() # persistent -> state revert changes made from every test_method ran

    ###########################
    ##  create_new_user  ##
    ###########################

    def test_create_new_user_valid_int_id(self):
        # email = "newtestemail@gmail.com"
        # password = "hashed_pw"
        user_id = self.repo.create_new_user(self.new_fake_email, self.new_fake_password)
        self.assertIsInstance(user_id, int)
        self.assertGreater(user_id, 0) # maybe shouldn't use serial pk lol


    def test_create_new_user_persists(self):
        """ verifying user exists in db """

        user_id = self.repo.create_new_user(self.new_fake_email, self.new_fake_password)
        created_user = db.session.get(User, user_id) # retrieves User instance if given valid pk

        self.assertIsNotNone(created_user)
        self.assertEqual(created_user.email, self.new_fake_email)

    def test_create_new_user_failure(self):
        """ verifying a new user doesn't get created/added to db if email used already exists in db """

        with self.assertRaises(RepositoryInternalError):
            self.repo.create_new_user(self.test_user.email, "6769420password")

     # future tests (?): password is X characters long, valid email checker?

    ###########################
    ##  get_user_id  ##
    ###########################
   
    def test_get_user_id_valid(self):
        actual = self.repo.get_user_id("faker@gmail.com")
        expected = 67
        self.assertEqual(actual, expected)

    def test_get_user_id_invalid(self):
        """ edge case where an invalid email is given """        
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.get_user_id("nonexistentemail@gmail.com")

    ###########################
    ##  get_user_info  ##
    ###########################

    def test_get_user_info_valid_fields(self):
        user_info = self.repo.get_user_info(self.test_user.email)

        self.assertEqual(user_info.get("id"), 67)
        self.assertEqual(user_info.get("passwd"), "hashed_passw123")
        self.assertEqual(user_info.get("token"), "34we56rt7y8u9iou8biyexew8irxyiew")
        self.assertEqual(user_info.get("acc_status"), 2) #normal user

    def test_get_user_info_invalid_email(self):
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.get_user_info("not_a_real_email@gmail.com")

    ###########################
    ##  Table schemas needing change or removal: UserPreferences, USER_ROLES
    #
    #   update_session_token()
    #   get_authenticated_user()
    #   get_user_id_from_jwt_and_email()
    #
    #  ^skipping methods above, JWT will be implemented correctly and do this heavy lifting ##
    # 
    #   Tests relating to Stations, UserPreferences and storing session tokens (again, JWT deal with that) will be done #   after some schema changes are done. seems like serial primary key is wack asf
    ###########################    
    
    def test_unique_email_exists(self):
        pass

    def test_unique_id_exists(self):
        pass

    def test_update_account_status(self):
        # protected admin route can handle updating account status for user_role table 
        pass

    def test_update_user_password(self):
        pass

    def test_update_user_times(self):
        pass

    def test_get_user_start_and_end_times(self):
        pass

if __name__ == '__main__':
    unittest.main()