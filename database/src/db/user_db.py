"""
User database layer 

This module handles all database CRUD operations for User and UserPreferences records
"""

from trackSense_db_commands import run_get_cmd, run_exec_cmd
from typing import Any

def create_new_user(email: str, password: str):
    run_exec_cmd(
        "INSERT INTO Users (email, passwd) VALUES (%s, %s)",
        (email, password),
    )
    
def get_user_id(email: str) -> int | None:
    user = run_get_cmd("SELECT id FROM Users WHERE email = %s", (email,))
    
    if not user:
        return None
    
    return user[0][0]

def get_user_info(email: str): #-> list[TupleRow]
    return run_get_cmd("SELECT * FROM Users WHERE email = %s", (email,))

def update_session_token(user_id: int, token: str):
    run_exec_cmd(
        "UPDATE Users SET token = %s WHERE id = %s", (token, user_id)
    )
    
def get_authenticated_user(email: str, token: str, return_info="*"):
    return run_get_cmd(
        "SELECT %s FROM Users WHERE email = %s AND token = %s", (return_info, email, token)
    )
    
def update_account_status(email: int, new_role: int):
    run_exec_cmd(
            "UPDATE Users SET acc_status = %s WHERE email = %s",
            (new_role, email),
        )
    
def update_user_password(user_id: int, hashed_password: str):
    update_password_sql = (
        "UPDATE users SET passwd = %(passwd_hash)s WHERE id = %(user_id)s;"
    )
    run_exec_cmd(
        update_password_sql, args={"passwd_hash": hashed_password, "user_id": user_id}
    )
    
def update_user_times(user_id: int, start_time: str, end_time: str):
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
    run_exec_cmd(sql, args=args)

# below is related to userpreferencesapi.py, they get user_id many different ways lol

def get_user_id_and_times_from_jwt_and_email(email: str, token: str) -> list[tuple[Any,...]]:
    sql = """
    SELECT id, starting_time, ending_time FROM Users WHERE email = %(email)s AND token = %(token)s
    """
    args = {
        "email": email,
        "token": token,
    }
    return run_get_cmd(sql,args)

def get_user_id_from_jwt_and_email(email:str, token: str) -> list[tuple[Any,...]]:
    sql = """
    SELECT id FROM Users WHERE email = %(email)s AND token = %(token)s
    """
    args = {
        "email": email,
        "token": token,
    }
    return run_get_cmd(sql,args)


def get_station_id_from_user_preferences(user_id: int) -> list[tuple[Any,...]]:
    sql = """
    SELECT station_id FROM UserPreferences WHERE user_id = %(user_id)s
    """
    args = {
        "user_id": user_id,
    }
    return run_get_cmd(sql,args)

def delete_user_preferences(user_id: int):
    sql = """
    DELETE FROM UserPreferences WHERE user_id = %(user_id)s
    """
    args = {
        "user_id": user_id,
    }
    run_exec_cmd(sql,args)

def create_user_station_preference(user_id: int, station_id: int):
    sql = """
    INSERT INTO UserPreferences (user_id, station_id) VALUES %(user_id)s, %(station_id)s)
    """
    args = {
        "user_id": user_id,
        "station_id": station_id,
    }
    run_exec_cmd(sql,args)