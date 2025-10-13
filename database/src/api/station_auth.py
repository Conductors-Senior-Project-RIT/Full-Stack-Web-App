from flask import jsonify
from flask_restful import Resource, reqparse
from db.trackSense_db_commands import *
import json, datetime, requests
import random, string, hashlib


class StationAuth(Resource):

    def get(self):
        sql = """
            SELECT id, station_name FROM Stations
        """
        resp = run_get_cmd(sql)
        return jsonify(resp)

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("station_name", type=str, default="unnamed")
        args = parser.parse_args()
        pw = self.generate_password_string()  # returns og password, and hashed password
        # todo: write sql script to add station to db
        sql = """
            INSERT INTO Stations (station_name, passwd) VALUES
            (%(station_name)s, %(passwd)s)
        """
        run_exec_cmd(sql, args={"station_name": args["station_name"], "passwd": pw[1]})
        print("yippee nothing broke")
        return jsonify({"password": pw[0]})

    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument("id", type=int)
        args = parser.parse_args()
        pw = self.generate_password_string()
        sql = """
            UPDATE Stations
            SET passwd = %(hashed_pw)s
            WHERE id = %(id)s
        """

        run_exec_cmd(sql, args={"hashed_pw": pw[1], "id": args["id"]})
        return jsonify({"new_pw": pw[0]})

    def generate_password_string(self):
        string_len = random.randint(10, 15)
        password_string = "".join(
            random.choice(string.ascii_uppercase + string.digits)
            for _ in range(string_len)
        )
        print(f"Raw password String: {password_string}")
        hasher = hashlib.new("sha256")
        hasher.update(password_string.encode())
        hashed_pw = hasher.hexdigest()
        print(f"hashed_pw: {hashed_pw}")
        return [password_string, hashed_pw]
