from flask import request
from flask_restful import Resource
from flask_jwt_extended import get_jwt_identity

from backend.src.global_core.decorators import role_required

from ..service.user_service import UserService

from backend.database import db

class UserPreferences(Resource):
    @role_required()
    def get(self):
        # Get user ID via JWT
        current_user_id = int(get_jwt_identity())
        session = db.session
        user_service = UserService(session)
        response = user_service.get_user_preferences(current_user_id)
        return response, 200

    @role_required()
    def post(self):
        # Get user ID via JWT
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        new_preferences = data.get("preferences", [])

        session = db.session
        user_service = UserService(session)
        user_service.reset_and_update_user_preferences(current_user_id, new_preferences)
        session.commit()
        return ({"message": "Preferences updated successfully"}), 200
