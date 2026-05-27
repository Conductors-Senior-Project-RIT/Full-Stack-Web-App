from flask import request
from flask_restful import Resource
from werkzeug.exceptions import BadRequest

from ..service.station_service import StationService
from backend.database import db

class StationOnline(Resource):
    def get(self):
        """Retrieves the time and/or date that the server received a ping notification from
        a station.

        Args:
            station_name (str): The name of the station to retrieve the last seen date
                and time for. Must be provided as a query parameter in the request URL.

        Raises:
            `BadRequest`: Raised when the station name is not provided as a parameter.

        Returns:
            Request: A datetime string under the key `last_seen`. If the date is within
                today, it is formatted as `HH: MM AM/PM`; otherwise, it is formatted as
                `MON DD, YYYY at HH:MM AM/PM`.
        """
        station = request.args.get("station_name", default=None, type=str)
        if station is None:
            raise BadRequest("Station name not provided!")

        # Create a request-specific database session
        session = db.session
        formatted_date = StationService(session).get_last_seen(station)

        # Return the last seen date of the station to the client
        return {"last_seen": formatted_date}, 200
    

    def post(self):
        """Updates the time and date a station pinged the server. This endpoint serves as
        the point a station can ping the server.

        Raises:
            `BadRequest`: Raised if station ID is not greater than 1.

        Returns:
            Request: A datetime string under the key `last_seen` that represents the
                time and date that the station pinged the server. If the date is within
                today, it is formatted as `HH: MM AM/PM`; otherwise, it is formatted as
                `MON DD, YYYY at HH:MM AM/PM`.
        """
        data = request.get_json()
        stat_id = int(data.get("station_id"))

        # All station IDs start at 1, so the provided station ID must be greater than or equal to 1
        if stat_id < 1:
            raise BadRequest(f"Station ID must be greater than or equal to 1, but ({stat_id}) was provided!")

        # Create a request-specific database session, update the last seen date of the station, and commit the changes to the database
        session = db.session
        formatted_date = StationService(session).update_last_seen(stat_id)
        session.commit()

        return {"last_seen": formatted_date}, 200 # flask requires some response object to be returned (here, its done under the hood)
