from flask import jsonify, request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from db.trackSense_db_commands import run_get_cmd, run_exec_cmd
from service.user_service import get_user_preferences, reset_and_update_user_preferences

"""
note: the error handling will be changed soon for everything user related
"""

class UserPreferences(Resource):
    @jwt_required()
    def get(self):
        # Get the current user's ID from the JWT
        current_user_id = int(get_jwt_identity())
        try:
            response = get_user_preferences(current_user_id)
            return response, 200
        except Exception as e:
            return jsonify({"message": str(e)}), 400

    @jwt_required()
    def post(self):
        # Get the current user's ID from the JWT
        current_user_id = int(get_jwt_identity())

        data = request.get_json()
        new_preferences = data.get("preferences", [])

        try:
            reset_and_update_user_preferences(current_user_id, new_preferences)
            return ({"message": "Preferences updated successfully"}), 200

        except Exception as e:
            return jsonify({"message": str(e)}), 400
