from flask import jsonify, request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from db.trackSense_db_commands import run_get_cmd, run_exec_cmd


class UserPreferences(Resource):
    @jwt_required()
    def get(self):
        # Get the current user's ID from the JWT
        current_user = get_jwt_identity()
        print("Current user:", current_user, flush=True)
        token = request.headers.get("Authorization").split()[1]
        user = run_get_cmd(
            """
            SELECT id, starting_time, ending_time FROM Users WHERE email = %s AND token = %s
            """,
            (current_user, token),
        )
        user_info = user[
            0
        ]  # this throws an error if someone tries to make a call without the api key
        # this also assumes we get exactly one response. Realistically, thats how it should work.
        start_time = user_info[1]
        end_time = user_info[2]
        # TODO: make a proper API call that will throw a code if nothing is found here
        print(user_info)
        preferences = run_get_cmd(
            """
            SELECT station_id FROM UserPreferences WHERE user_id = %s
            """,
            (user_info[0],),
        )

        # Fetch all stations
        stations = run_get_cmd(
            """
            SELECT id, station_name FROM Stations
            """
        )

        # Format the response
        preferences_set = {pref[0] for pref in preferences}
        response = [
            {
                "station_id": station[0],
                "station_name": station[1],
                "selected": station[0] in preferences_set,
                "start_time": start_time.strftime("%H:%M"),
                "end_time": end_time.strftime("%H:%M"),
            }
            for station in stations
        ]

        return response, 200

    @jwt_required()
    def post(self):
        # Get the current user's ID from the JWT
        current_user = get_jwt_identity()
        print("Current user:", current_user, flush=True)
        token = request.headers.get("Authorization").split()[
            1
        ]  # Get the token from the request header
        user = run_get_cmd(
            """
            SELECT id FROM Users WHERE email = %s AND token = %s
            """,
            (current_user, token),
        )
        user_id = user[0][0] if user else None  # Get the user ID from the database
        if not user_id:
            return jsonify({"message": "Invalid user or token"}), 401

        data = request.get_json()
        new_preferences = data.get("preferences", [])

        # Clear the user's existing preferences
        run_exec_cmd(
            """
            DELETE FROM UserPreferences WHERE user_id = %s
            """,
            (user_id,),
        )

        # Insert the new preferences into the UserPreferences table
        for station_id in new_preferences:
            run_exec_cmd(
                """
                INSERT INTO UserPreferences (user_id, station_id) VALUES (%s, %s)
                """,
                (user_id, station_id),
            )

        return ({"message": "Preferences updated successfully"}), 200
