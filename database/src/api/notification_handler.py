from flask import jsonify
from flask_restful import Resource, reqparse
from db.trackSense_db_commands import *
import json, datetime
import http.client, urllib
import os
from dotenv import *

load_dotenv()


class NotificationService(Resource):
    """
    example code from Pushover API documentation
    import http.client, urllib
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
    urllib.parse.urlencode({
        "token": "APP_TOKEN",
        "user": "USER_KEY",
        "message": "hello world",
    }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()
    """

    def post(self):

        load_dotenv()
        TOKEN = os.getenv("Pushover_Token")

        # get params from request
        parser = reqparse.RequestParser()
        parser.add_argument("userid", default="", type=str)
        parser.add_argument("stationname", default="UNKNOWN", type=str)
        args = parser.parse_args()

        def_string = f"A train was just logged at {args['stationname']}. Please check and validate this information."
        user_id = args["userid"]

        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request(
            "POST",
            "/1/messages.json",
            urllib.parse.urlencode(
                {
                    "token": TOKEN,
                    "user": user_id,
                    "title": "Tracksense Notification",
                    "message": def_string,
                }
            ),
            {"Content-type": "application/x-www-form-urlencoded"},
        )
        conn.getresponse()
        return
