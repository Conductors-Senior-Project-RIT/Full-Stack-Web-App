from flask import current_app

from backend.test.conftest import BaseTestCase

class TestApp(BaseTestCase):
    def test_app_created(self):
        assert self.app is not None
        assert current_app == self.app

    def test_client_exists(self):
        response = self.client.get("/")
        # Depending on your app, this might return 404 if no route
        assert response.status_code in (200, 404)