import hashlib
import secrets
from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash

from db.database_core import *
from service.service_core import *
from db.station_repo import StationRepository
from db.user_repo import UserRepository
from service.email_service import send_welcome_email, send_forgot_password_email

"""
TODO: move everything from user_db.py to user_repo.py for custom error handling!
"""
class UserService(BaseService):
    def __init__(self, session):
        self._user_repo = UserRepository(session)
        self._station_repo = StationRepository(session)
    
    def register_user(self, email: str, password: str):
        """
        After a user signs up, by default they have all stations set as their default preference

        TODO: remove auto incrementing from DB for "id" field and instead generate UUID here (maybe)
        TODO: somehow check that an email is valid (has @ symbol etc)
        repo/db layer should do the indexing for us, frick i forgot ... too lazy to change it rn will do later
        """
        hashed_password = generate_password_hash(password)

        self._user_repo.create_new_user(email, hashed_password)

        user_id = self._user_repo.get_user_id(email)

        self.initialize_user_preferences(user_id) #default user settings

        email_sent = send_welcome_email(email)

        return {"user_id": user_id, "email_sent": email_sent}

    def initialize_user_preferences(self, user_id: int):
        """
        Default trains a user is subscribed to. Inserts all stations into the UserPreferences table for the new user
        """
        stations = self._station_repo.get_stations() # returns list of dictionaries

        if not stations: # if empty, etc
            raise RuntimeError("No train stations available")

        for station in stations:
            station_id = station.get("id")
            self._user_repo.create_user_station_preference(user_id, station_id)

    def is_registered(self, email: str, password: str):
        """
        Validates user password, if nothing is returned something went wrong
        """
        user = self._user_repo.get_user_info(email)

        if not user: # invalid email as there's no rows returned
            return None

        user_hashed_password = user[0][2] #list of tuple, 3rd element is passwd

        if check_password_hash(user_hashed_password, password):  # validates user password
            return user

        return None

    def update_user_role(self, email: str, new_role: str):
        """
        If none is returned, that means user email doesn't exist in our database. Hence, user must sign up
        """
        if self._user_repo.get_user_id(email) is None: #  trying to elevate role for this specific email does not exist
            return None

        self._user_repo.update_account_status(email, int(new_role)) #must cast role to int as "additional_claims" from JWT only accepts that or something else that was funky and i don't remember

        return True

    def create_user_password_reset_token(self, email):
        """
        Creates a password reset token for a user to reset their current password.
        """

        user_id = self._user_repo.get_user_id(email)

        if user_id is None: # no such email exists in our db, at some point we should introduce a logger and this is the perfect example of putting it in our code
            return

        reset_token = secrets.token_urlsafe(32) #remove the 32 argument?
        hashed_token = hashlib.sha256(reset_token.encode()).hexdigest()

        self._user_repo.create_user_reset_token(user_id, hashed_token)

        send_forgot_password_email(email, reset_token)

    def is_user_password_reset_token_valid(self, token):
        """
        move this elsewhere?
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        return len(self._user_repo.get_user_id_from_valid_reset_request_token(token_hash)) > 0 # if no password reset token found, then 0 rows are returned, and vice versa

    def reset_user_password(self, reset_token, password):
        token_hash = hashlib.sha256(reset_token.encode()).hexdigest()

        user_id = self._user_repo.get_user_id_from_valid_reset_request_token(token_hash)

        if not user_id: # list of tuples returned is empty; so user doesn't exist
            # log that user cannot be found for a password reset
            # return a custom made service error for passwords so it can be used  for testing --> user_repo.py
            return False # --> replace this to raise custom error for cleaner tests!

        # everything below should work because it's simple sql statements
        hashed_password = generate_password_hash(password)

        user_id = user_id[0][0]

        self._user_repo.update_user_password(user_id, hashed_password)

        self._user_repo.delete_user_id_from_reset_requests(user_id) #after resetting password, delete the user id from the reset requests table

        return True

    def get_user_preferences(self, user_id: int):
        """
        todo: create class for custom error handling, just rushing through this so i can get testing ready to go lol
        todo: also... this is all can be done in 1 sql query... bruh
        """
        station_preferences = self._user_repo.get_station_id_from_user_preferences(user_id)

        all_stations = self._station_repo.get_stations()

        starting_time, ending_time = self._user_repo.get_user_start_and_end_times(user_id) #unpack tuple

        # Format the response
        preferences_set = {pref[0] for pref in station_preferences}
        response = [
            {
                "station_id": station.get("id"),
                "station_name": station.get("name"),
                "selected": station.get("id") in preferences_set,
                "start_time": starting_time.strftime("%H:%M"),
                "end_time": ending_time.strftime("%H:%M"),
            }
            for station in all_stations
        ]

        return response

    def reset_and_update_user_preferences(self, user_id: int, new_station_preferences):
        self._user_repo.delete_user_preferences(user_id)

        for station_id in new_station_preferences:
            self._user_repo.create_user_station_preference(user_id, station_id)


