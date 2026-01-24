from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, reqparse
import json, datetime, requests

from db.trackSense_db_commands import run_exec_cmd, run_get_cmd


class PushoverUpdater(Resource):
    @jwt_required()
    def get(self):
        resp = None
        parser = reqparse.RequestParser()
        parser.add_argument("token", default=None, type=str)
        parser.add_argument("pushover_id", default=None, type=str)
        args = parser.parse_args()

        if (args["token"] == None or args["pushover_id"] == None):
            print("Invalid info provided")
            return 400

        sql_args = {
            "auth_token": args["token"],
            "pushover_id": args["pushover_id"]
        }
        sql_update = """
                                SELECT * FROM Users
                                WHERE token = %(auth_token)s
                                """

        resp = run_exec_cmd(sql_update, sql_args)
        print(resp)
        return jsonify(
            [
                {
                    "id": tup[0],
                    "email": tup[1],
                    "password": tup[2],
                    "token": tup[3],
                    "accStatus": tup[4],
                    "pushover": tup[5],
                }
                for tup in resp
            ]
        )
        return 200

    @jwt_required()
    def post(self):

        # Get the current user's ID from the JWT
        current_user = get_jwt_identity()
        print("Current user:", current_user, flush=True)
        token = request.headers.get("Authorization").split()[
            1
        ]  # Get the token from the request header
        user = run_get_cmd(
            """
            SELECT id FROM Users WHERE email = %s AND token = %s
            """,
            (current_user, token),
        )
        user_id = user[0][0] if user else None  # Get the user ID from the database
        if not user_id:
            return jsonify({"message": "Invalid user or token"}), 401

        resp = None
        parser = reqparse.RequestParser()
        parser.add_argument("pushover_id", default=None, type=str)
        args = parser.parse_args()

        if(args["pushover_id"] == None):
            print("Invalid info provided")
            return 400

        sql_args = {
            "user_id":user_id,
            "pushover_id":args["pushover_id"]
        }
        sql_update = """
                        UPDATE Users
                        SET pushover_id = %(pushover_id)s 
                        WHERE id = %(user_id)s
                        """

        resp = run_exec_cmd(sql_update, sql_args)
        print(resp)

        return ({"message": "Pushover Id updated successfully"}), 200
