import unittest

from backend import create_app

class TestUserApiUnit(unittest.TestCase):
    """
    Unit tests for user blueprint routes
    """

    def setUp(self) -> None:
        """
        Fresh instance of app in testing mode + test client created before every test method  
        """
        self.app = create_app("test")
        self.client = self.app.test_client()

    ###########################
    ##  register route ##
    ###########################

    def test_register_user_success(self):
        pass

    def test_register_invalid_email(self):
        pass

    def test_register_invalid_password(self):
        pass

    def test_register_email_already_exists(self):
        pass

    ###########################
    ##  login route ##
    ###########################

    def test_login_user_success(self):
        pass

    def test_login_user_invalid_password(self):
        pass
    
    def test_login_user_invalid_email(self):
        pass

    def test_login_nonexistent_user(self):
        pass

    ###########################
    ##  logout route ##
    ###########################


    ###########################
    ##  forgot-password, validate-reset-token, reset-password routes ##
    ###########################

    ###########################
    ##  elevate-user route ##
    ###########################

    ###########################
    ##  user_preferences/time route ##
    ###########################

if __name__ == '__main__':
    unittest.main()