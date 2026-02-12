"""
User database layer 

This module handles all database CRUD operations for User and UserPreferences records
"""
from psycopg import OperationalError, Error

from database_core import *
from trackSense_db_commands import run_get_cmd, run_exec_cmd
from typing import Any

"""
todo: refactor repository to include error handling 
from db.station_repo import get_stations
from db.user_db 
check how caleb does the imports for the repos

todo: then refactory service for error handling 
again see how caleb inherits his base service class and throws errors

todo: rewrite logic with session?
"""
class UserRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session)

    def create_new_user(self, email: str, password: str):
        try:
            run_exec_cmd(
                "INSERT INTO Users (email, passwd) VALUES (%s, %s)",
                (email, password),
            )
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Issue creating a new user: {e}")
        
    def get_user_id(self, email: str) -> int | RepositoryInternalError:
        user = run_get_cmd("SELECT id FROM Users WHERE email = %s", (email,))
        try:
            if not user:
                raise RepositoryNotFoundError(email) # technically this shouldn't ever happen (?)
        
            return user[0][0]

        except IndexError as e:
            raise RepositoryParsingError(str(e))
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError("Could not retrieve user id.")

    def get_user_info(self, email: str): #-> list[TupleRow]

        try:
            user = run_get_cmd("SELECT * FROM Users WHERE email = %s", (email,))

            if not user:
                raise RepositoryNotFoundError(email)# technically this shouldn't ever happen (?)

        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Could not retrieve user info: {e}")

    def update_session_token(self, user_id: int, token: str): # remove most likely, web tokens handled via JWT
        run_exec_cmd(
            "UPDATE Users SET token = %s WHERE id = %s", (token, user_id)
        )
        
    def get_authenticated_user(self, email: str, token: str, return_info="*"): # remove most likely, web tokens handled via JWT
        return run_get_cmd(
            "SELECT %s FROM Users WHERE email = %s AND token = %s", (return_info, email, token)
        )
        
    def update_account_status(self, email: str, new_role: int):
        try:
            run_exec_cmd(
                    "UPDATE Users SET acc_status = %s WHERE email = %s",
                    (new_role, email),
                )
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Issue updating account status: {e}")
        
    def update_user_password(self, user_id: int, hashed_password: str):
        update_password_sql = (
            "UPDATE users SET passwd = %(passwd_hash)s WHERE id = %(user_id)s;"
        )

        try:
            run_exec_cmd(
                update_password_sql, args={"passwd_hash": hashed_password, "user_id": user_id}
            )
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Issue updating user credentials: {e}")
        
    def update_user_times(self, user_id: int, start_time: str, end_time: str):
        sql = """
            UPDATE Users
            SET starting_time = %(start_time)s,
            ending_time = %(ending_time)s
            WHERE id = %(uid)s
        """
        args = {
            "start_time": start_time,
            "ending_time": end_time,
            "uid": user_id,
        }
        try:
            run_exec_cmd(sql, args=args)
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Issue updating user times (user preferences related?): {e}")


    # below is related to userpreferencesapi.py, they get user_id many different ways lol

    def get_user_start_and_end_times(self, user_id: int) -> tuple[Any,...]:
        sql = """
        SELECT starting_time, ending_time FROM Users WHERE id = %(user_id)s
        """
        args = {
            "user_id": user_id,
        }
        try:
            user_start_and_end_times = run_get_cmd(sql,args)[0] #just return tuple as there's only 1 row within the list of tuples

            if not user_start_and_end_times: #empty tuple
                raise RepositoryNotFoundError(user_id)

            return user_start_and_end_times

        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Could not get user start and end times: {e}") # technically this shouldn't ever happen (?)


    def get_user_id_from_jwt_and_email(self, email:str, token: str) -> list[tuple[Any,...]]: # remove maybe as we don't need to store jwt in db (same reasoning as above)
        sql = """
        SELECT id FROM Users WHERE email = %(email)s AND token = %(token)s
        """
        args = {
            "email": email,
            "token": token,
        }
        return run_get_cmd(sql,args)


    def get_station_id_from_user_preferences(self, user_id: int) -> list[tuple[Any,...]]:
        sql = """
        SELECT station_id FROM UserPreferences WHERE user_id = %(user_id)s
        """
        args = {
            "user_id": user_id,
        }
        try:
            station_id = run_get_cmd(sql,args)

            if not user_id:
                raise RepositoryNotFoundError(user_id)

            return station_id
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Could not retrieve station id from user's preferences: {e}")

    def delete_user_preferences(self, user_id: int):
        sql = """
        DELETE FROM UserPreferences WHERE user_id = %(user_id)s
        """
        args = {
            "user_id": user_id,
        }
        try:
            run_exec_cmd(sql,args)
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Issue deleting a user's preference: {e}")

    def create_user_station_preference(self, user_id: int, station_id: int):
        sql = """
        INSERT INTO UserPreferences (user_id, station_id) VALUES %(user_id)s, %(station_id)s)
        """
        args = {
            "user_id": user_id,
            "station_id": station_id,
        }
        try:
            run_exec_cmd(sql,args)
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Issue adding a station id to a user's preference {e}")


    def create_user_reset_token(self, user_id, hashed_token):
        """
        TODO: Move helpers like this function and the ones below somewhere else
        """
        reset_token_sql = """
                INSERT INTO reset_requests (uid, token, expiration) VALUES 
                (%(user_id)s, %(token_hash)s, NOW() + INTERVAL '1 hour');
                """
        try:
            run_exec_cmd(
                reset_token_sql, args={"user_id": user_id, "token_hash": hashed_token}
            )
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Issue adding a reset request token: {e}")

# the two methods below may need to be rewritten as I don't see the purpose of storing token hashes especially as we need to refresh the JWT to avoid fast auto logouts...

    def get_user_id_from_valid_reset_request_token(self, token_hash):
        """
        look into later
        """
        validate_token_sql = """
                SELECT u.id FROM reset_requests as r
                INNER JOIN users AS u ON r.uid = u.id
                WHERE r.token = %(token_hash)s AND r.expiration >= NOW();
            """
        # results = run_get_cmd(validate_token_sql, args={"token_hash": token_hash})
        return run_get_cmd(validate_token_sql, args={"token_hash": token_hash})

    def delete_user_id_from_reset_requests(self, user_id):
        delete_request = "DELETE FROM reset_requests WHERE uid = %(user_id)s;"
        run_exec_cmd(delete_request, args={"user_id": user_id})