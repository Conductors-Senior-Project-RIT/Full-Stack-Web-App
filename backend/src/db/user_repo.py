"""
User database layer

This module handles all database CRUD operations for User and UserPreferences records.
This includes (but is not limited to): account creation, preference management, and the password reset token lifecycle
"""

from typing import Any

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, ScalarResult
from sqlalchemy.exc import SQLAlchemyError

from .db_core.models import User
from .db_core.repository import BaseRepository
from .db_core.exceptions import (
    wrap_repository_error_handler,
    REPOSITORY_ERROR_MAP,
    RepositoryInternalError,
    RepositoryError,
    RepositoryNotFoundError,
)


class UserRepository(BaseRepository):
    """A database interface for User and UserPreferences record operations

    Raw SQL queries are wrapped for the 'Users', 'UserPreferences', and 'reset_requests' tables.

    Args:
        BaseRepository: Inherits generic CRUD helpers that 'User' can leverage and extend upon.
    """
    def __init__(self, session):
        super().__init__(User, session)
        # UserRepository methods are wrapped with the wrap_repository_error_handler decorator when the class is instantiatied
        for attr, value in self.__dict__.items():
            if callable(value):
                if attr == "session" or attr.startswith("_") or not callable(value):
                    continue  # don't override session attribute; causes AttributeError when doing self.session.execute(): 'function' object has no attribute 'execute'
                wrapped = wrap_repository_error_handler(value)
                setattr(self, attr, wrapped)

    def _construct_email_not_found(self, email: str) -> RepositoryNotFoundError:
        return RepositoryNotFoundError(
            caller_name=self.__class__.__name__,
            message=f"Could not find a user with an email = {email}",
            show_error=False,
        )

    def _construct_id_not_found(self, user_id: int) -> RepositoryNotFoundError:
        return RepositoryNotFoundError(
            caller_name=self.__class__.__name__,
            message=f"Could not find a user with an ID = {user_id}",
            show_error=False,
        )

    def create_new_user(self, email: str, password: str) -> int:
        """Inserts a new user record and returns the generated primary key

        Args:
            email (str): user's normalized email address
            password (str): user's bcrypt hashed password

        Returns:
            int: the newly created user primary key

        Raises RepositoryInternalError: if the INSERT fails then there was a constraint violation on the 'email' field.
        """
        
        sql = """
            INSERT INTO Users (email, passwd) 
            VALUES (:email, :password)
            RETURNING id
        """
        args = {"email": email, "password": password}

        try:
            result = self.session.execute(
                text(sql), args
            ).scalar_one()  # error comes from unqiue constraint on emails
            return result
        except SQLAlchemyError as e:
            raise RepositoryInternalError(
                caller_name=self.__class__.__name__,
                message="An error occurred creating a new user!",
                show_error=True,
            ) from e

    def unique_email_exists(self, email: str):
        """Raises an error if no user with the provided email exists

        Method acts as a guard before operations that require an existing user.

        Raises:
            RepositoryNotFoundError: if no matching email is found
        """

        sql = text("SELECT COUNT(1) FROM Users WHERE email = :email")
        result = self.session.execute(sql, {"email": email}).scalar_one()
        if result == 0:
            raise self._construct_email_not_found(email)

    def email_exists(self, email: str) -> bool:
        """Returns True if an account/user with the provided email exists, False otherwise
        """

        sql = text("SELECT COUNT(1) FROM Users WHERE email = :email")
        result = self.session.execute(sql, {"email": email}).scalar_one()
        return result > 0  # >0 because returning count

    def unique_id_exists(self, user_id: int):
        """Raises an error if no user with the provided ID exists.

        Method acts as a guard before operations that require an existing user.

        Args:
            user_id(int): user primary key to check

        Raises:
            RepositoryNotFoundError: if no user with the given 'user_id' is found.
        """

        sql = text("SELECT COUNT(1) FROM Users WHERE id = :user_id")
        result = self.session.execute(sql, {"user_id": user_id}).scalar_one()
        if result == 0:
            raise self._construct_id_not_found(user_id)

    def get_user_id(self, email: str) -> int:
        """Returns the primary key of the user with the given email
        """

        sql = text("SELECT id FROM Users WHERE email = :email")
        user = self.session.execute(sql, {"email": email}).scalar_one_or_none()

        if user is None:
            raise self._construct_email_not_found(email)

        return user

    def get_user_info(self, email: str) -> dict:
        """Returns all columns for the user with the given email as a dictionary

        Args:
            email (str): email address to look up.

        Returns:
            dict: column names mapped to values for the matching row

        Raises:
            RepositoryNotFoundError: if no user with provided email exists.
        """

        sql = text("SELECT * FROM Users WHERE email = :email")
        user = self.session.execute(sql, {"email": email}).one_or_none()

        if not user:
            raise self._construct_email_not_found(email)

        return user._asdict()  # leftoff here; finish user_service that uses this lol; im at login() part now

    def update_account_status(self, email: str, new_role: int) -> int:
        """Updates the 'acc_status' (role) of a user with the provided email

        Args:
            email (str): The email address of the user to update.
            new_role (int): The new role value to assign.

        Returns:
            int: The updated 'acc_status' value.

        Raises:
            RepositoryNotFoundError: if no user with 'email' exists.
            RepositoryInternalError: if the UPDATE produces no changes.
        """

        # Check if user exists, will raise exception otherwise
        self.unique_email_exists(email)

        sql = """
            UPDATE Users 
            SET acc_status = :role 
            WHERE email = :email
            RETURNING acc_status
        """

        result = self.session.execute(
            text(sql), {"role": new_role, "email": email}
        ).scalar_one_or_none()
        if result is None:
            raise RepositoryInternalError(
                self.__class__.__name__,
                message="An error occurred updating account status, 0 changes made!",
                show_error=True,
            )

        return result

    def update_user_password(self, user_id: int, hashed_password: str) -> int:
        """A user's password is replaced with a new one.

        Args:
            user_id (int): the primary key of the user to update.
            hashed_password (str): the new hashed password to use now.

        Returns:
            int: The updated user's primary key

        Raises:
            RepositoryNotFoundError: If no user with 'user_id' exists.
            RepositoryInternalError: if an UPDATE produces no changes.
        """

        # Check if user exists, will raise exception otherwise.
        self.unique_id_exists(user_id)

        sql = """
            UPDATE Users 
            SET passwd = :passwd_hash 
            WHERE id = :user_id
            RETURNING id
        """

        result = self.session.execute(
            text(sql), {"passwd_hash": hashed_password, "user_id": user_id}
        ).scalar_one_or_none()

        if not result:
            raise RepositoryInternalError(
                self.__class__.__name__,
                message="An error occurred updating password, 0 changes made!",
                show_error=True,
            )

        return result

    def update_user_times(
        self, user_id: int, start_time: str, end_time: str
    ) -> tuple[str, str]:
        """Updates the notification start and end times for a user

        Args:
            user_id (int): The primary key of the user to update
            start_time (str): The new notification start time
            end_time (str): The new notification end time

        Returns:
            tuple[str, str]: The updated (starting_time, ending_time) values

        Raises:
            RepositoryNotFoundError: If no user with the provided 'user_id' exists
            RepositoryInternalError: If the UPDATE produces no changes
        """
        # Check if user exists, will raise exception otherwise.
        self.unique_id_exists(user_id)

        sql = """
            UPDATE Users
            SET starting_time = :start_time, ending_time = :ending_time
            WHERE id = :uid
            RETURNING starting_time, ending_time
        """
        args = {
            "start_time": start_time,
            "ending_time": end_time,
            "uid": user_id,
        }

        result = self.session.execute(text(sql), args).one_or_none()
        if result is None:
            raise RepositoryInternalError(
                self.__class__.__name__,
                message="An error occurred updating user times, 0 changes made!",
                show_error=True,
            )

        return result.starting_time, result.ending_time

    # below is related to userpreferencesapi.py, they get user_id many different ways lol
    def get_user_start_and_end_times(self, user_id: int) -> tuple[int, int]:
        """Returns the notification window (start and end) times for a given user (user_id)

        Args:
            user_id (int): The primary key of the user to query.

        Returns:
            tuple[int, int]: The (starting_time, ending_time) values

        Raises:
            RepositoryNotFoundError: If no user with 'user_id' exists.
        """

        sql = text("SELECT starting_time, ending_time FROM Users WHERE id = :user_id")
        args = {"user_id": user_id}

        user_times = self.session.execute(sql, args).one_or_none()

        if user_times is None:  # Incorrectly sized results
            raise self._construct_id_not_found(user_id)

        return user_times.starting_time, user_times.ending_time

    def get_station_id_from_user_preferences(self, user_id: int) -> list:
        """Returns all station IDs in a user's preference list.

        Args:
            user_id (int): The primary key of the user to query

        Returns:
            list: Row objects each containing a 'station_id'

        Raises:
            RepositoryNotFoundError: If no user with 'user_id' exists.
        """

        # Check if a single user with provided id exists, otherwise raise exception
        self.unique_id_exists(user_id)

        sql = text("SELECT station_id FROM UserPreferences WHERE user_id = :user_id")
        args = {"user_id": user_id}

        return self.session.execute(sql, args).all()

    def delete_user_preferences(self, user_id: int) -> ScalarResult[Any]:
        """Deletes all preference rows for a given user and returns the removed station IDs

        Args:
            user_id (int): The primary key of the user whose preferences will be deleted.

        Returns:
            ScalarResult[Any]: The 'station_id' values that were deleted.
        """

        sql = """
            DELETE FROM UserPreferences
            WHERE user_id = :user_id
            RETURNING station_id
        """
        args = {"user_id": user_id}

        return self.session.execute(text(sql), args).scalars()

    def create_user_station_preference(self, user_id: int, station_id: int):
        """Inserts a single station preference row in a user's preference list.

        Args:
            user_id (int): The primary key of the user.
            station_id (int): The station ID to add to the user's preference list

        Raises:
            RepositoryInternalError: If the INSERT produces no result
        """
         
        sql = """
            INSERT INTO UserPreferences (user_id, station_id) 
            VALUES (:user_id, :station_id)
            RETURNING station_id
        """
        args = {"user_id": user_id, "station_id": station_id}

        result = self.session.execute(text(sql), args).scalar_one_or_none()
        if not result:
            raise RepositoryInternalError(
                self.__class__.__name__,
                message="An error occurred creating new user preference, 0 additions made!",
                show_error=True,
            )

    def create_user_reset_token(self, user_id, hashed_token):
        """Stores a hashed password reset token with a 1 hour expiration.

        Args:
            user_id (int): The primary key of the user requesting a password reset token 
            hashed_token (str): The hex digest of the raw password reset token

        Raises:
            RepositoryInternalError: If the INSERT produces no result.
        """

        sql = """
            INSERT INTO reset_requests (uid, token, expiration) 
            VALUES (:user_id, :token_hash, NOW() + INTERVAL '1 hour')
            RETURNING id
        """
        args = {"user_id": user_id, "token_hash": hashed_token}

        result = self.session.execute(text(sql), args).scalar_one_or_none()
        if not result:
            raise RepositoryInternalError(
                self.__class__.__name__,
                message="An error occurred creating new reset token, no token created!",
                show_error=False,
            )

    def get_user_id_from_valid_reset_request_token(self, token_hash) -> int | None:
        """Returns the user ID associated with a valid, unexpired reset token

        Args:
            token_hash (str): The hex digest of the raw password reset token

        Returns:
            int | None: The matching user's ID, or None if the token is invalid or expired
        """

        sql = """
            SELECT u.id FROM reset_requests as r
            INNER JOIN Users AS u ON r.uid = u.id
            WHERE r.token = :token_hash AND r.expiration >= NOW();
        """
        return self.session.execute(
            text(sql), {"token_hash": token_hash}
        ).scalar_one_or_none()

    def delete_user_id_from_reset_requests(self, user_id: int):
        """Removes all password reset request rows for a given user.

        Called after a successful password reset to invalidate used tokens.

        Args:
            user_id (int): The primary key of the user whose password reset token(s) we wish to delete.
        """

        sql = "DELETE FROM reset_requests WHERE uid = :user_id RETURNING id;"
        self.session.execute(text(sql), {"user_id": user_id})
