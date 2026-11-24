from flask import request
from flask_restful import Resource
from werkzeug.exceptions import BadRequest, Unauthorized

from backend.database import db

from flask_jwt_extended import get_jwt, jwt_required
from ..service.station_service import StationService


class StationPasswd(Resource):
    """Flask REST resource for retrieving a station's password."""

    @jwt_required()
    def get(self):
        """Returns the password of a station given its ID.

        Args:
            station_id (int): The ID of the station to retrieve the password of.

        Returns:
            Response: Returns the password of the station.
        """
        stat_id = request.args.get("station_id", default=None, type=int)

        # Gets the role of the user
        claims = get_jwt()
        user_role = claims.get("user_role")

        if (user_role == 0):
            # Raise an error if no ID is provided
            if stat_id == None:
                raise BadRequest("No station ID provided!")

            # Flask creates a request-specific database session
            session = db.session

            # Get the password of the station
            password = StationService(session).get_station_passwd(stat_id)
            
            return {"password": password}, 200
        else:
            raise Unauthorized(description="User is not an admin!")
