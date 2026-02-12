from flask import jsonify, request
from flask_restful import Resource, reqparse
from werkzeug.exceptions import BadRequest
from db.trackSense_db_commands import *
from backend.src.service.record_service import RecordService
from backend.db import db
import datetime
import http.client, urllib
from dotenv import *

load_dotenv()


def validate_int_argument(value: int, name: str, min_value: int):
    if not isinstance(value, int):
        raise BadRequest(f"{name} ({value}) is not an integer!")
    if value < min_value:
        raise BadRequest(f"Provided {name} must be greater than {min_value} but was given {value}...")

class HistoryDB(Resource):
    def get(self):
        """
        Returns train records of a specified type using provided request parameters.
        "typ": Specifies what type of train record(s) to return. 1: EOT, 2: HOT, 3: DPU (default -1: collection of EOT)
        "id": The id of a train record to retrieve.
        "page": The page of records to return.

        Returns:
            Response: Returns an individual train record response payload with a status code. Response payload may include a
            collection of EOT records if "type" is -1.
        """
        # Argument checking goes here
        typ = request.args.get("type", default=-1, type=int)
        id = request.args.get("id", default=-1, type=int)
        page = request.args.get("page", default=1, type=int)

        # Check our type and page arguments (typ checked in strategy creation)
        validate_int_argument(id, "type", 1)
        validate_int_argument(page, "page", 1)
        
        session = db.session
        
        th_service = RecordService(session, typ)
        results = th_service.get_train_history(typ, id, page)
        return jsonify(results), 200
            

        

    def post(self):
        """
        Inserts a new train record of a specified type into the database.

        Returns:
            Response: Returns the status code of the request.
        """
        resp = None
        date_rec = datetime.datetime.now()
        dt_str = date_rec.strftime("%Y-%m-%d %H:%M:%S")
        
        parser = reqparse.RequestParser()
        parser.add_argument("date_rec", default=None, type=str)
        parser.add_argument("type", default=-1, type=int)
        parser.add_argument("station_id", default=0, type=int)
        parser.add_argument("symbol_id", type=str, default=None)
        parser.add_argument("unit_addr", type=str, default="")
        parser.add_argument("brake_pressure", type=str, default="")
        parser.add_argument("motion", type=str, default="")
        parser.add_argument("marker_light", type=str, default="")
        parser.add_argument("turbine", type=str, default="")
        parser.add_argument("battery_cond", type=str, default="")
        parser.add_argument("battery_charge", type=str, default="")
        parser.add_argument("arm_status", type=str, default="")
        parser.add_argument("signal_strength", type=float, default=0)
        parser.add_argument("frame_sync", type=str, default="")
        parser.add_argument("command", type=str, default="")
        parser.add_argument("checkbits", type=str, default="")
        parser.add_argument("parity", type=str, default="")
        args = vars(parser.parse_args())
        
        # right now this has 0 authentication. Too bad!
        typ = args["type"]
        
        session = db.session
            
        th_service = RecordService(session, typ)
        results = th_service.post_train_history(typ, args, dt_str)
        return jsonify(results), 200
        


        # if not resp:
        #     print(recovery_request)
        #     print(typ)
        #     self.add_new_pin(args["station_id"], typ, args["unit_addr"])
        #     noti = self.check_for_notification(
        #         args["unit_addr"], args["station_id"], args["type"]
        #     )
        #     # print(noti)
        #     if not noti and not recovery_request:
        #         # print("owo") # lmfao wha
        #         self.notif_send(args["station_id"])
                
        return 200
    

    def delete(self):  # not sure if this is needed
        print("delete goes here!")
        return

    def put(self):  # Not needed - if this is called then idk what happened
        print("put goes here!")
        return

    def notif_send(self, laptop_id):
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
