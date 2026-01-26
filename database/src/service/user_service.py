from werkzeug.security import check_password_hash, generate_password_hash

from db.station_repo import get_stations
from db.user_db import create_new_user, get_user_id, create_user_station_preference, get_user_info
from service.email_service import send_welcome_email


def register_user(email: str, password: str):
    """
    After a user signs up, by default they have all stations set as their default preference
    Error handling
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

    if not user: #invalid email
        return None

    user_hashed_password = user[0][2] #list of tuple, 3rd element is passwd

    if check_password_hash(user_hashed_password, password): # validates user password
        return user

    return None


