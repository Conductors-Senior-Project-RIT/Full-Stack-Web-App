from flask import jsonify, request
from flask_restful import Resource, reqparse
from db.trackSense_db_commands import *
from database.src.service.train_history_service import TrainHistoryService
from database.src.service.service_status import ServiceError
import datetime
import http.client, urllib
from dotenv import *

load_dotenv()


def validate_int_argument(value: int, name: int, min_value: int):
    if not isinstance(value, int):
        raise ValueError(f"{name} ({value}) is not an integer!")
    if value < min_value:
        raise ValueError(f"Provided {name} must be greater than {min_value} but was given {value}...")

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
        
        try:
            # Check our type and page arguments (typ checked in strategy creation)
            validate_int_argument(id, "type", 1)
            validate_int_argument(page, "page", 1)
            
            th_service = TrainHistoryService(typ)
            results = th_service.get_train_history(typ, id, page)
            return jsonify(results), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except RuntimeError as e:
            return jsonify({"error": str(e)}), 500
        

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
        try:
            th_service = TrainHistoryService(typ)
            results = th_service.post_train_history(typ, args, dt_str)
            return jsonify(results), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except ServiceError as e:
            return jsonify({"error": str(e)}), 500
        

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

    def add_new_pin(self, station_id, typ, unit_addr):  #

        self.attempt_auto_fill_info(unit_addr, typ)
        if typ == 1:

            resp_eot_id = self.get_newest_eot_id(unit_addr)

            update_args = {"id": resp_eot_id, "unit_addr": unit_addr}
            sql_update = """
            UPDATE EOTRecords
            SET most_recent = false
            WHERE id != %(id)s and unit_addr = %(unit_addr)s and most_recent = true
            """

            resp = run_exec_cmd(sql_update, update_args)
            print(resp)

        elif typ == 2:  # TODO: Test once rest of HOT signals in train history are fixed

            resp_hot_id = self.get_newest_hot_id(unit_addr)

            update_args = {"id": resp_hot_id, "unit_addr": unit_addr}
            sql_update = """
                        UPDATE HOTRecords
                        SET most_recent = false
                        WHERE id != %(id)s and unit_addr = %(unit_addr)s and most_recent = true
                        """

            resp = run_exec_cmd(sql_update, update_args)
            print(resp)

        return

    def get_newest_eot_id(self, unit_addr):
        sql_eot_id = """SELECT id FROM EOTRecords WHERE 
                                              unit_addr = %(unit_addr)s
                                               """
        sql_eot_id_args = {"unit_addr": unit_addr}
        resp_eot_id = run_get_cmd(sql_eot_id, sql_eot_id_args)
        return resp_eot_id[len(resp_eot_id) - 1][0]

    def get_newest_hot_id(self, unit_addr):
        sql_hot_id = """SELECT id FROM HOTRecords WHERE 
                                              unit_addr = %(unit_addr)s
                                               """
        sql_hot_id_args = {"unit_addr": unit_addr}
        resp_hot_id = run_get_cmd(sql_hot_id, sql_hot_id_args)
        return resp_hot_id[len(resp_hot_id) - 1][0]

    def attempt_auto_fill_info(self, unit_addr, typ):
        symb = self.check_for_symbol(unit_addr, typ)
        engi = self.check_for_engi(unit_addr, typ)
        if symb != None:
            if typ == 1:
                id = self.get_newest_eot_id(unit_addr)
                sql_update = """
                                    UPDATE EOTRecords
                                    SET symbol_id = %(symb_id)s
                                    WHERE id = %(id)s
                                    """
                update_param = {"symb_id": symb, "id": id}

                resp = run_exec_cmd(sql_update, update_param)
            if typ == 2:
                id = self.get_newest_hot_id(unit_addr)
                sql_update = """
                                                    UPDATE HOTRecords
                                                    SET symbol_id = %(symb_id)s
                                                    WHERE id = %(id)s
                                                    """
                update_param = {"symb_id": symb, "id": id}

                resp = run_exec_cmd(sql_update, update_param)
        else:
            print("No Symbol to Update")

        if engi != None:
            if typ == 1:
                id = self.get_newest_eot_id(unit_addr)
                sql_update = """
                                    UPDATE EOTRecords
                                    SET engine_num = %(engi_id)s
                                    WHERE id = %(id)s
                                    """
                update_param = {"engi_id": engi, "id": id}

                resp = run_exec_cmd(sql_update, update_param)
            if typ == 2:
                id = self.get_newest_hot_id(unit_addr)
                sql_update = """
                                                    UPDATE HOTRecords
                                                    SET engine_num = %(engi_id)s
                                                    WHERE id = %(id)s
                                                    """
                update_param = {"engi_id": engi, "id": id}

                resp = run_exec_cmd(sql_update, update_param)
        else:
            print("No Engine Number to Update")

        return

    def check_for_symbol(self, unit_addr, typ):
        if typ == 1:
            sql_eot_symb = """SELECT symbol_id FROM EOTRecords WHERE 
                                unit_addr = %(unit_addr)s and most_recent = True
                                """
            sql_param = {"unit_addr": unit_addr}

            resp = run_get_cmd(sql_eot_symb, sql_param)
            if len(resp) > 0:
                return resp[0][0]

        if typ == 2:
            sql_hot_symb = """SELECT symbol_id FROM HOTRecords WHERE 
                                unit_addr = %(unit_addr)s and most_recent = True
                                """
            sql_param = {"unit_addr": unit_addr}

            resp = run_get_cmd(sql_hot_symb, sql_param)
            if len(resp) == 1:
                return resp[0][0]

        return None

    def check_for_engi(self, unit_addr, typ):
        if typ == 1:
            sql_eot_engi = """SELECT engine_num FROM EOTRecords WHERE 
                                unit_addr = %(unit_addr)s and most_recent = True
                                """
            sql_param = {"unit_addr": unit_addr}

            resp = run_get_cmd(sql_eot_engi, sql_param)
            if len(resp) > 0:
                return resp[0][0]

        if typ == 2:
            sql_hot_engi = """SELECT engine_num FROM HOTRecords WHERE 
                                unit_addr = %(unit_addr)s and most_recent = True
                                """
            sql_param = {"unit_addr": unit_addr}

            resp = run_get_cmd(sql_hot_engi, sql_param)
            if len(resp) == 1:
                return resp[0][0]

        return None

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
