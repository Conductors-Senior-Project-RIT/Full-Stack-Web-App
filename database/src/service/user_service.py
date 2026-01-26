from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash

from db.station_repo import get_stations
from db.user_db import create_new_user, get_user_id, create_user_station_preference, get_user_info, \
    update_account_status
from service.email_service import send_welcome_email

def register_user(email: str, password: str):
    """
    After a user signs up, by default they have all stations set as their default preference

    TODO: remove auto incrementing from DB for "id" field and instead generate UUID here.
    """
    hashed_password = generate_password_hash(password)

    create_new_user(email, hashed_password)

    user_id = get_user_id(email)
    if not user_id:
        raise RuntimeError("Error creating a user")

    initialize_user_preferences(user_id) #default user settings

    email_sent = send_welcome_email(email)

    return {"user_id": user_id, "email_sent": email_sent}

def initialize_user_preferences(user_id: int):
    """
    Default trains a user is subscribed to. Inserts all stations into the UserPreferences table for the new user
    """
    stations = get_stations() # returns list of dictionaries

    if not stations: # if empty, etc
        raise RuntimeError("No train stations available")

    for station in stations:
        station_id = station.get("id")
        create_user_station_preference(user_id, station_id)

def is_registered(email: str, password: str):
    """
    Validates user password, if nothing is returned something went wrong
    """
    user = get_user_info(email)

    if not user: # invalid email
        return None

    user_hashed_password = user[0][2] #list of tuple, 3rd element is passwd

    if check_password_hash(user_hashed_password, password):  # validates user password
        return user

    return None

def update_user_role(email: str, new_role: str):
    """
    If none is returned, that means user email doesn't exist in our database. Hence, user must sign up
    """
    if get_user_id(email) is None: #  trying to elevate role for this specific email does not exist
        return None

    update_account_status(email, int(new_role)) #must cast role to int as "additional_claims" from JWT only accepts that or something else that was funky and i don't remember

    return True


