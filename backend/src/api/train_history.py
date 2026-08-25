import http.client
import urllib

from flask import request
from flask_restful import Resource, reqparse
from werkzeug.exceptions import BadRequest

from backend.database import db
from backend.src.service.record_service import RecordService

from ..db.trackSense_db_commands import *

# load_dotenv()


class HistoryDB(Resource):
    """These endpoints deal mostly with retrieving EOT and HOT records. The creation of
    these records lies in the stations receiving the radio data. The users then access
    the data stored in the database.
    """
    
    def get(self):
        """Returns a singular record depending on the signal type and ID provided. The
        parameters should be provided as query parameters in the request URL.

        Args:
            type (int): The type of the train record that is being retrieved. EOT: `1`,
            HOT: `2`, DPU: `3`. Currently, DPU is not supported.
            id (int): The ID of the train record to retrieve.

        Returns:
            Response: Returns individual train record data with a status code.
        """
        typ = request.args.get("type", default=-1, type=int)
        id = request.args.get("id", default=-1, type=int)

        # Check our type and page arguments, type is checked in service constructor.
        if id < 1:
            raise BadRequest(f"Record ID must be greater than 1! Provided: {id}")
        
        # Create a request-specific database session, call the record service to retrieve the train record
        session = db.session
        service = RecordService(session, typ)
        results = service.get_train_record(id)
        
        # The service already returns a JSON-serializable response, so just return the result
        return results, 200
            

    def post(self):
        """Adds new record to the database. 
        
        Additionally, handles logic for updating the
        map pins to know which signals are the most recently detected with that unit
        address. The notification system was broken when we received the project;
        however, the request should also determine whether input data warrants sending a
        notification, and then make the appropriate calls to notify users about the new
        train data.

        The parameters should be provided in the request body as a JSON object.

        Returns:
            Response: Returns the status code of the request.
        """
        parser = reqparse.RequestParser()
        parser.add_argument("date_rec", default=None, type=str)
        parser.add_argument("type", default=-1, type=int)
        parser.add_argument("station_id", default=0, type=int)
        parser.add_argument("symbol_id", type=int, default=None)
        parser.add_argument("unit_addr", type=str, default=None)
        parser.add_argument("brake_pressure", type=str, default=None)
        parser.add_argument("motion", type=str, default=None)
        parser.add_argument("marker_light", type=str, default=None)
        parser.add_argument("turbine", type=str, default=None)
        parser.add_argument("battery_cond", type=str, default=None)
        parser.add_argument("battery_charge", type=str, default=None)
        parser.add_argument("arm_status", type=str, default=None)
        parser.add_argument("signal_strength", type=float, default=0)
        parser.add_argument("frame_sync", type=str, default=None)
        parser.add_argument("command", type=str, default=None)
        parser.add_argument("checkbits", type=str, default=None)
        parser.add_argument("parity", type=str, default=None)
        args = dict(parser.parse_args())
        
        # 'station_recorded' is the correct column name in the database, 
        # but we use 'station_id' as the argument name in the request body for clarity
        args["station_recorded"] = args["station_id"]
        typ = args.pop("type")
        
        # Create a request-specific database session
        session = db.session

        # Call the record service to create a new train record, and commit the changes to the database if successful
        service = RecordService(session, typ)
        new_id = service.create_train_record(args)
        session.commit()
        
        return new_id, 201
    

    # TODO: Below is the follow code for the old notification system, which is currently unused. 
    # We will need to update this code to work with the new notification system once it is implemented.
    def notif_send(self, laptop_id):
        """CURRENTLY NOT USED, DO NOT TEST. NEED NEW NOTI SYSTEM"""
        sql = """
            SELECT user_id, pushover_id from UserPreferences
            INNER JOIN Users on Users.id = user_id
            WHERE station_id = %(loc_id)s
            AND Users.starting_time <= CURRENT_TIME::TIME WITH TIME ZONE
            AND Users.ending_time >= CURRENT_TIME::TIME WITH TIME ZONE
        """
        users = run_get_cmd(sql, args={"loc_id": laptop_id})
        print(users)
        pushover_token = os.getenv("Pushover_Token")
        print(pushover_token)
        location_name = run_get_cmd(
            "SELECT station_name FROM Stations WHERE id = %(laptop_id)s",
            args={"laptop_id": laptop_id},
        )[0][0]
        def_string = f"A train was just logged at {location_name}. Please check and validate this information."
        for tup in users:
            conn = http.client.HTTPSConnection("api.pushover.net:443")
            conn.request(
                "POST",
                "/1/messages.json",
                urllib.parse.urlencode(
                    {
                        "token": pushover_token,
                        "user": tup[1],
                        "title": "FollowThatFred Notification",
                        "message": def_string,
                    }
                ),
                {"Content-type": "application/x-www-form-urlencoded"},
            )
        resp = conn.getresponse()
        print(resp.status)
        return


    def check_for_notification(self, unit_addr, station_id, typ):
        """CURRENTLY NOT USED, DO NOT TEST. NEED NEW NOTI SYSTEM"""
        # print("here")
        # check if there are any recent trains logged with this unit address and station id
        # if one was logged within the last 10 minutes, return True
        # else return false
        # Typ == type - since type is a function in python we use typ

        # TODO: add logic to actually check for stuff
        if typ == 1:  # EOT
            sql = """
                SELECT * FROM EOTRecords
                WHERE unit_addr = %(unit_address)s AND station_recorded = %(station_id)s AND date_rec >= NOW() - INTERVAL '10 minutes'
            """
            resp = run_get_cmd(
                sql, args={"unit_address": unit_addr, "station_id": station_id}
            )
            # print(len(resp))
            if len(resp) > 1:  # arbitrary number that will make this work
                return True
        if typ == 2:  # HOT
            sql = """
                SELECT * FROM HOTRecords
                WHERE unit_addr = %(unit_address)s AND station_recorded = %(station_id)s AND date_rec >= NOW() - INTERVAL '10 minutes'
            """
            resp = run_get_cmd(
                sql, args={"unit_address": unit_addr, "station_id": station_id}
            )
            if len(resp) > 1:  # arbitrary number that will make this work
                return True
        return False
