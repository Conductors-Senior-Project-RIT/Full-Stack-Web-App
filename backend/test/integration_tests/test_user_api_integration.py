import unittest
from backend.test.base_test_case import BaseTestCase
from backend.database import db

class TestUserApiIntegration(BaseTestCase):
    """
    Integration tests for user blueprint routes

    flow: http request -> route -> service -> repo -> database -> response back to client

    self.client: shared state across test methods, starts off unauthenticated, used for unprotected routes
    self.app.test_client(): create a new isolated client via test_client() for tests testing auth state/ cookies
    """

    # @classmethod
    # def setUpClass(cls):
    #     super().setUpClass() 
    #     cls.client = cls.app.test_client() # reusable test client for anything non-cookies related

    @classmethod
    def tearDownClass(cls):
        db.drop_all() # avoids polluting test db 
        return super().tearDownClass()

    ###########################
    ##  helpers  ##
    ###########################

    def _registered_client(self, email=None, password="default_pass"):
        """
        New client (registered user here) is created and exists in db but NOT logged in (so no cookie set). 
        """
        email = email or self._unique_email()
        client = self.app.test_client()
        client.post('/api/register', json={
            'email': email,
            'password': password
        })
        return client, email, password

    def _logged_in_client(self, email=None, password="default_pass"):
        """
        Registers a new client/user and logs them in. JWT cookie is set on the client now, subsequent erquest 
        """
        client, email, password = self._registered_client(email,password)
        client.post('/api/login', json={
            'email': email,
            'password': password
        })
        return client, email
    
    def _new_client(self):
        """
        Returns raw unauthenitcaed client with no state
        Use for: unprotected routes, or veryifing routes reject unauthenticated/unauthorized requests
        """
        return self.app.test_client()

    def _unique_email(self):
        """
        creates email from the test method's name
        """
        return f"{self._testMethodName}@gmail.com"

    ###########################
    ##  register route ##
    ###########################

    def test_register_user_success(self):
        client = self._new_client()
        email = self._unique_email()
        password = 'hashed_pswd'
        response = client.post('/api/register', json={
            'email': email,
            'password': password
        })
        self.assertEqual(response.status_code, 201)

    def test_register_missing_email(self):
        response = self._new_client().post('/api/register', json={
            'password': "wewqe12323"
        })
        self.assertEqual(response.status_code, 400)

    def test_register_missing_password(self):
        response = self._new_client().post('/api/register', json={
            'email': 'johndoe@gmail.com',
        })
        self.assertEqual(response.status_code, 400)

    def test_register_duplicate_email(self):
        _, email, _ = self._registered_client() # creates first registree
        response = self._new_client().post('/api/register', json={'email': email, 'password': "B0!nsdyyu"}) # creating second registree
        self.assertEqual(response.status_code, 400)
    
    ###########################
    ##  login route ##
    ###########################

    def test_login_user_success(self):
        client, email, password = self._registered_client() # register client
        response = client.post('/api/login', json={ # login registered client
            'email': email,
            'password': password
        })

        self.assertIsNotNone(client.get_cookie("access_token_cookie")) # checks that cookie was set after logging in | default value for JWT_ACCESS_COOKIE_NAME 
        self.assertEqual(response.status_code, 200)

    def test_login_user_wrong_password(self):
        client, email, _ = self._registered_client() 
        response = client.post('/api/login', json={ 
            'email': email,
            'password': "WRONGGGGGGGGGGGG_PASSSORRRRRRRRRSBFSYUFAF"
        })
        self.assertEqual(response.status_code, 401)

    def test_login_nonexistent_user(self):
        response = self._new_client().post('/api/login', json={
            'email': "idontexisttttt@gmail.com", 
            "password": "notthepassword123"
        })
        self.assertEqual(response.status_code, 401)


    ###########################
    ##  logout route ##
    ###########################

    def test_logout_success(self):
        pass

    def test_logout_without_access_token(self):
        pass
    

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