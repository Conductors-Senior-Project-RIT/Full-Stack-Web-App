import hashlib
import secrets

from email_validator import validate_email, EmailNotValidError

from backend.src.db.db_core.exceptions import RepositoryNotFoundError
from werkzeug.exceptions import BadRequest
# from werkzeug.security import check_password_hash, generate_password_hash

from ... import bcrypt
from .service_core import BaseService
from ..db.station_repo import StationRepository
from ..db.user_repo import UserRepository
from ..service.email_service import email_service #instantiated 

class UserService(BaseService):
    """Service layer for user account and preference managemennt

    Coordinates between 'UserRepository' and 'StationRepository' to implement
    registration, authentication, password reset, role management, and
    station preference operations.

    Args:
        BaseService: Inherits the base service interface
    """
    def __init__(self, session):
        self._user_repo = UserRepository(session)
        self._station_repo = StationRepository(session)
    
    def _normalize_email(self, email: str) -> str | None:
        try:
            return validate_email(email, check_deliverability=False).normalized
        except EmailNotValidError:
            return None

    def register_user(self, email: str, password: str):
        """Registers a new user, initializes the default preferences and sends a confirmation email.

        Normalizes the email, hashes the password, creates the user record,
        and subscribes the new user to all existing stations by default

        Args:
            email (str): The raw email address provided by the user.
            password (str): The plaintext password to hash and store.

        Raises:
            BadRequest: If the email format is invalid or already registered.
        """

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        email = self._normalize_email(email)
        if not email:
            raise BadRequest("Invalid email format")

        if self._user_repo.email_exists(email): 
            raise BadRequest("Email already registered")
        
        print("Email does not exist")

        user_id = self._user_repo.create_new_user(email, hashed_password)

        self.initialize_user_preferences(user_id) #default user settings
        
        # Temporarily avoid this until we create email sender again

        email_service.send_registered_email(email) 
        # return {"user_id": user_id}

    def is_registered(self, email: str, password: str):
        """Validates login credentials and returns user info if successful

        Args:
            email (str): The email address to authenticate
            password (str): The plaintext password to verify against the stored hash

        Returns:
            dict | None: The user info dictionary if credentials are valid, None otherwise
        """

        email = self._normalize_email(email)
        if not email:
            return None

        try:
            user = self._user_repo.get_user_info(email) 
        except RepositoryNotFoundError:
            return None

        user_hashed_password = user.get("passwd")

        if bcrypt.check_password_hash(user_hashed_password, password):
            return user

        return None
    
    "bottom functions not tested yet"
    
    def update_user_role(self, email: str, new_role: str):
        """Updates the role of a user with the given email

        Args:
            email (str): The email address of the user to update.
            new_role (str): The new role value as a string (must cast to int beforehand).

        Raises:
            RepositoryNotFoundError: If no user exists for the provided email.
        """

        self._user_repo.get_user_id(email) # 
            
        self._user_repo.update_account_status(email, int(new_role)) # cast role to int as "additional_claims" from JWT only accepts that or something else that was funky and i don't remember

    def create_user_password_reset_token(self, email):
        """Generates and stores a password reset token, then emails it to the user.

        Returns silently without error if the email is invalid or not registered
        to avoid leaking account existence information.

        Args:
            email (str): The email address of the password reset requester.
        """
        email = self._normalize_email(email)
        if not email:
            return
        
        try:
            user_id = self._user_repo.get_user_id(email)
        except RepositoryNotFoundError:
            return # route will always respond with 200 to not let someone know if an email is registered up or not

        reset_token = secrets.token_urlsafe(32) # why 32 lol
        hashed_token = hashlib.sha256(reset_token.encode()).hexdigest() # copy pasted the previous group's old functionality

        self._user_repo.create_user_reset_token(user_id, hashed_token)

        email_service.send_forgot_password_email(email, reset_token)

    def is_user_password_reset_token_valid(self, token):
        """Checks whether a password reset token is valid and unexpired.

        Args:
            token (str): The raw reset token from the email link.

        Returns:
            bool: True if the token maps to a valid, unexpired entry.
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        return self._user_repo.get_user_id_from_valid_reset_request_token(token_hash) is not None # if no password reset token found, then None rows are returned; otherwise, id is returned

    def reset_user_password(self, reset_token, password):
        """Resets a user's password using a valid password reset token.

        Hashes the new password, updates the current stored password hash, and deletes the used
        reset token to prevent more than 1 reset per token.

        Args:
            reset_token (str): The password reset token from the email link.
            password (str): The new plaintext password to hash and store.

        Returns:
            bool: True if successful, False if reset token is invalid or expired.
        """
        token_hash = hashlib.sha256(reset_token.encode()).hexdigest()

        user_id = self._user_repo.get_user_id_from_valid_reset_request_token(token_hash)

        if user_id is None: # user doesn't exist
            # log that user cannot be found for a password reset
            return False

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        # hashed_password = generate_password_hash(password) reverting back to old hashing algorithm

        self._user_repo.update_user_password(user_id, hashed_password)

        self._user_repo.delete_user_id_from_reset_requests(user_id) #after resetting password, delete the user id from the reset requests table

        return True

    def update_user_times(self, user_id: int, start_time: str, end_time: str):
        """Updates the notification window (start and end) times for a user.

        Args:
            user_id (int): The primary key of the user to update
            start_time (str): The new notification start time
            end_time (str): The new notification end time
        """
        self._user_repo.update_user_times(user_id, start_time, end_time)

    def initialize_user_preferences(self, user_id: int):
        """Subscribes a new user to all existing stations by default.

        Inserts one 'UserPreferences' row per station for a given user.

        Args:
            user_id (int): The primary key of the newly created user

        Raises:
            RuntimeError: If no stations exist in the database
        """
        stations = self._station_repo.get_stations() # returns list of dictionaries

        if not stations: # if empty, etc
            raise RuntimeError("No train stations available")

        for station in stations:
            station_id = station.get("id")
            self._user_repo.create_user_station_preference(user_id, station_id)

    def get_user_preferences(self, user_id: int):
        """Returns all stations in a user's preference list and ataches their notifcation window times for each selected station entry

        Args:
            user_id (int): The primary key of the user to query

        Returns:
            list[dict]: Each dict contains 'station_id', 'station_name', 'selected',
                'start_time', and 'end_time'
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
        """Replaces a user's preferences list with a brand new preference list.

        Deletes all existing preferences for a user and inserts the provided station IDs.

        Args:
            user_id (int): The primary key of the user to update.
            new_station_preferences (list[int]): The new station IDs to subscribe to.
        """
        self._user_repo.delete_user_preferences(user_id)

        for station_id in new_station_preferences:
            self._user_repo.create_user_station_preference(user_id, station_id)