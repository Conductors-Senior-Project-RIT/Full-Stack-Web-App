from flask_restful import Resource, reqparse
from werkzeug.exceptions import BadRequest

from backend.database import db
from backend.src.service.station_service import StationService


class StationAuth(Resource):
    def get(self):
        """Returns a complete list of station IDs and names in the database.

        Returns:
            Response: Returns an array of ID and name pairs in JSON objects if the
                retrieval was successful; otherwise, an error message is returned.
        """
        # Flask creates a request-specific database session
        session = db.session
        
        # Get all station ids and names from the database as a collection of dictionaries
        results = StationService(session).get_stations()
        
        return results, 200

    def post(self):
        """Creates a new station with a randomly generated password in the database with
        the provided the name of a new station.

        Args:
            station_name (str): The name of the new station to be created. Default:
                "unnamed"

        Returns:
            Response: Returns the password of the new station if the station's creation
                was successful; otherwise, an error message is returned.
        """
        parser = reqparse.RequestParser()
        parser.add_argument("station_name", type=str, default="unnamed")
        args = parser.parse_args()
        
        # Flask creates a request-specific database session
        session = db.session
        
        # Creates a new station with the given name, and returns the generated password associated with it
        pw = StationService(session).create_station(args["station_name"])
        
        # Commit the changes if everything is successful
        session.commit()
        
        # Return the new password to the user
        return {"password": pw}, 201
      
      
    def put(self):
        """Updates a station's password in the database specified by a provided station ID.

        Args:
            id (int): The ID of the station to update the password of. Must be greater
                than 0.

        Returns:
            Response: Returns the new password of the specified station if the station's
                update was successful; otherwise, an error message is returned.
        """
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int, default=-1)
        args = parser.parse_args()
        
        # Ensure that the primary key of the station is valid
        if args["id"] < 1:
            raise BadRequest("An invalid station ID was provided!")
        
        # Flask creates a request-specific database session
        session = db.session
        
        # Returns the updated station password
        pw = StationService(session).update_station_password(args["id"])
        
        # Commit the changes if everything is successful
        session.commit()
        
        # Return the updated password to the user
        return {"new_pw": pw}, 200
