from flask import jsonify
from flask_restful import Resource, reqparse
from db.trackSense_db_commands import *
from db.station_db import get_station_id_name_pairs, create_new_station, update_station_password
import json, datetime, requests
import random, string, hashlib


class StationAuth(Resource):
    def get(self):
        """Returns a list of station IDs and names under the following fields "id" and "name".

        Returns:
            Response: Returns a collection of ID and name pairs if the retrieval was successful; otherwise,
            an error message is returned.
        """
        results = get_station_id_name_pairs()
        if not results:
            return jsonify({"error": "Error occured while retrieving station IDs and names."}), 500
        return jsonify(results), 200

    def post(self):
        """Creates a new station with a password in the database provided the name of a new station.

        Returns:
            Response: Returns the password of the new station if the station's creation was successful; otherwise,
            an error message is returned.
        """
        parser = reqparse.RequestParser()
        parser.add_argument("station_name", type=str, default="unnamed")
        args = parser.parse_args()
        unhashed_pw, hashed_pw = self.generate_password_string()  # returns og password, and hashed password
        
        # Create the station and return the result of the operation
        result = create_new_station(args["station_name"], hashed_pw)
        if not result:
            return jsonify({"error": "Error occurred when creating a new station."}), 500
        
        print("yippee nothing broke")
        return jsonify({"password": unhashed_pw}), 200  # Maybe a bad idea to send over an unhashed password lol

    def put(self):
        """Updates a station's password in the database specified by a provided station ID.

        Returns:
            Response: Returns the new password of the specified station if the station's update was successful; otherwise,
            an error message is returned.
        """
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, default=-1)
        args = parser.parse_args()
        unhashed_pw, hashed_pw = self.generate_password_string()
        
        if args["id"] == -1:
            return jsonify({"error": "A station ID was not provided!"}), 400
        
        # Update the station's password and return the result of the operation
        result = update_station_password(args["id"], hashed_pw)
        if not result:
            return jsonify({"error": "An error occurred while updating the station's password."}), 500
        return jsonify({"new_pw": unhashed_pw}), 200

    def generate_password_string(self) -> tuple:
        string_len = random.randint(10, 15)
        password_string = "".join(
            random.choice(string.ascii_uppercase + string.digits)
            for _ in range(string_len)
        )
        print(f"Raw password String: {password_string}")
        hasher = hashlib.new("sha256")
        hasher.update(password_string.encode())
        hashed_pw = hasher.hexdigest()
        print(f"hashed_pw: {hashed_pw}")
        return password_string, hashed_pw
