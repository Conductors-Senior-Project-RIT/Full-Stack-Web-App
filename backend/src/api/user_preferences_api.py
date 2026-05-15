from flask import request
from flask_restful import Resource
from flask_jwt_extended import get_jwt_identity

from backend.src.api.api_core.decorators import role_required

from ..service.user_service import UserService

from backend.database import db

class UserPreferences(Resource):
    """Flask REST resource for retrieving and updating user station preferences.
    """

    @role_required()
    def get(self):
        """Returns an authenticated user's station preferences and notification start and end times.

        Returns: Response with a payload containing a list of a user's station preference items and an HTTP status code.
        """
        # Get user ID via JWT
        current_user_id = int(get_jwt_identity())
        session = db.session
        user_service = UserService(session)
        response = user_service.get_user_preferences(current_user_id)
        return response, 200

    @role_required()
    def post(self):
        """Replaces an authenticated user's station preferences by deleting all existing preferences and inserting the new preferences. The default Empty list value clears all preferences

        Returns: Response with a message and HTTP status code
        """
        # Get user ID via JWT
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        new_preferences = data.get("preferences", [])

        session = db.session
        user_service = UserService(session)
        user_service.reset_and_update_user_preferences(current_user_id, new_preferences)
        session.commit()
        return ({"message": "Preferences updated successfully"}), 200
