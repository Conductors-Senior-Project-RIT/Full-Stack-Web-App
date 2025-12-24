from flask import jsonify
from flask_restful import Resource, reqparse
from database.src.service.service_status import ServiceError
import database.src.service.station_service as station_service


class StationAuth(Resource):
    def get(self):
        """Returns a list of station IDs and names under the following fields "id" and "name".

        Returns:
            Response: Returns a collection of ID and name pairs if the retrieval was successful; otherwise,
            an error message is returned.
        """
        try:  
            results = station_service.get_stations()
            return jsonify(results), 200
        except ServiceError as e:
            return jsonify({"error": str(e)}), 500

    def post(self):
        """Creates a new station with a password in the database provided the name of a new station.

        Returns:
            Response: Returns the password of the new station if the station's creation was successful; otherwise,
            an error message is returned.
        """
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("station_name", type=str, default="unnamed")
            args = parser.parse_args()
            
            pw = station_service.create_station(args["station_name"])
            return jsonify({"password": pw}), 200
        
        except ServiceError as e:
            return jsonify({"error", str(e)}), 500
      
      
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
            return jsonify({"error": "An invalid station ID was provided!"}), 400
        
        try:
            pw = station_service.update_station_password(args["id"])
            return jsonify({"new_pw": pw}), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        except ServiceError as e:
            return jsonify({"error": str(e)}), 500
