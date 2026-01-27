import hashlib
import secrets
from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash

from db.station_repo import get_stations
from db.user_db import create_new_user, get_user_id, create_user_station_preference, get_user_info, \
    update_account_status, create_user_reset_token, get_user_id_from_valid_reset_request_token, update_user_password, \
    delete_user_id_from_reset_requests
from service.email_service import send_welcome_email, send_forgot_password_email

"""
TODO: move everything from user_db.py to user_repo.py for custom error handling!
"""

def register_user(email: str, password: str):
    """
    After a user signs up, by default they have all stations set as their default preference

    TODO: remove auto incrementing from DB for "id" field and instead generate UUID here (maybe)
    TODO: somehow check that an email is valid (has @ symbol etc)
    repo/db layer should do the indexing for us, frick i forgot ... too lazy to change it rn will do later
    """
    hashed_password = generate_password_hash(password)

    create_new_user(email, hashed_password)

    user_id = get_user_id(email)
    if user_id is None:
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

    if not user: # invalid email as there's no rows returned
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

def create_user_password_reset_token(email):
    """
    Creates a password reset token for a user to reset their current password.
    """

    user_id = get_user_id(email)

    if user_id is None: # no such email exists in our db, at some point we should introduce a logger and this is the perfect example of putting it in our code
        return

    reset_token = secrets.token_urlsafe(32) #remove the 32 argument?
    hashed_token = hashlib.sha256(reset_token.encode()).hexdigest()

    create_user_reset_token(user_id, hashed_token)

    send_forgot_password_email(email, reset_token)

def is_user_password_reset_token_valid(token):
    """
    move this elsewhere?
    """
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    return len(get_user_id_from_valid_reset_request_token(token_hash)) > 0 # if no password reset token found, then 0 rows are returned, and vice versa

def reset_user_password(reset_token, password):
    token_hash = hashlib.sha256(reset_token.encode()).hexdigest()

    user_id = get_user_id_from_valid_reset_request_token(token_hash)

    if not user_id: # list of tuples returned is empty; so user doesn't exist
        # log that user cannot be found for a password reset
        # return a custom made service error for passwords so it can be used  for testing --> user_repo.py
        return False # --> replace this to raise custom error for cleaner tests!

    # everything below should work because it's simple sql statements
    hashed_password = generate_password_hash(password)

    user_id = user_id[0][0]

    update_user_password(user_id, hashed_password)

    delete_user_id_from_reset_requests(user_id) #after resetting password, delete the user id from the reset requests table

    return True


