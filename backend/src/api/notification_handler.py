from flask_restful import Resource, reqparse
from ..db.trackSense_db_commands import *
import http.client, urllib
import os
import requests

class NotificationService(Resource):

    def post(self):

        # get params from request
        parser = reqparse.RequestParser()
        parser.add_argument("station_id", default=0, type=int)
        args = parser.parse_args()

        location_name = run_get_cmd(
            "SELECT station_name FROM Stations WHERE id = %(laptop_id)s",
            args={"laptop_id": args["station_id"]},
        )[0][0]

        def_string = f"A train was just logged at {location_name}. Please check and validate this information."

        res = requests.put(
            "http://tracksense.se.rit.edu:6161/followthatfred",
            data=def_string,
            headers={ "Title": "Train spotted." }
        )

        return f"Successful: {res.ok}", 200 if res.ok else 500
