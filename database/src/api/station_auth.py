from flask import jsonify
from flask_restful import Resource, reqparse
from database.src.service.station_service import StationService
from database.src.service.service_core import *
from db.db import db


class StationAuth(Resource):
    def get(self):
        """Returns a list of station IDs and names under the following fields "id" and "name".

        Returns:
            Response: Returns a collection of ID and name pairs if the retrieval was successful; otherwise,
            an error message is returned.
        """
        session = db.session
        results = StationService(session).get_stations()
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
        
        session = db.session
        
        pw = StationService(session).create_station(args["station_name"])
        return jsonify({"password": pw}), 200
      
      
    def put(self):
        """Updates a station's password in the database specified by a provided station ID.

        Returns:
            Response: Returns the new password of the specified station if the station's update was successful; otherwise,
            an error message is returned.
        """
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, default=-1)
        args = parser.parse_args()
        
        if args["id"] < 1:
            return jsonify({"error": "An invalid station ID was provided!"}), 400
        
        session = db.session
        pw = StationService(session).update_station_password(args["id"])
        return jsonify({"new_pw": pw}), 200
