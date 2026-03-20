"""
User database layer 

This module handles all database CRUD operations for User and UserPreferences records
"""
from typing import Any

from sqlalchemy import text, ScalarResult

from backend.database import User
from .database_core import (
    layer_error_handler, REPOSITORY_ERROR_MAP, BaseRepository,
    RepositoryInternalError, RepositoryError, RepositoryNotFoundError
)

class UserRepository(BaseRepository):
    model = User
    
    def __init__(self, session):
        super().__init__(session)
        for attr, value in self.__dict__.items():
            if callable(value):
                if attr == "session":
                    continue #don't override session attribute; causes AttributeError when doing self.session.execute(): 'function' object has no attribute 'execute'
                wrapped = layer_error_handler(
                    func=value, 
                    error_map=REPOSITORY_ERROR_MAP, 
                    base_exception=RepositoryInternalError,
                    exclude=RepositoryError
                )
                setattr(self, attr, wrapped)


    def _construct_email_not_found(self, email: str) -> RepositoryNotFoundError:
        return RepositoryNotFoundError(
            caller_name=self.__class__.__name__,
            message=f"Could not find a user with an email = {email}",
            show_error=False
        )

    def _construct_id_not_found(self, user_id: int) -> RepositoryNotFoundError:
        return RepositoryNotFoundError(
            caller_name=self.__class__.__name__,
            message=f"Could not find a user with an ID = {user_id}",
            show_error=False
        )

    def create_new_user(self, email: str, password: str) -> int:
        sql = """
            INSERT INTO Users (email, passwd) 
            VALUES (:email, :password)
            RETURNING id
        """
        args = {"email": email, "password": password}
        
        result = self.session.execute(text(sql), args).scalar_one_or_none()
        if not result:
            raise RepositoryInternalError(
                caller_name=self.__class__.__name__,
                message="An error occurred creating a new user!",
                show_error=True
            )
        
        return result


    def unique_email_exists(self, email: str):
        sql = text("SELECT COUNT(1) FROM Users WHERE email = :email")
        result = self.session.execute(sql, {"email": email}).scalar_one()
        if result == 0:
            raise self._construct_email_not_found(email)
            
        
    def unique_id_exists(self, user_id: int):
        sql = text("SELECT COUNT(1) FROM Users WHERE id = :user_id")
        result = self.session.execute(sql, {"user_id": user_id}).scalar_one()
        if result == 0:
            raise self._construct_id_not_found(user_id)

    
    def get_user_id(self, email: str) -> int:
        sql = text("SELECT id FROM Users WHERE email = :email")
        user = self.session.execute(sql, {"email": email}).scalar_one_or_none()
        
        if user is None: # python treats the integer 0 as falsy, hence the change
            raise self._construct_email_not_found(email) # technically this shouldn't ever happen (?)
    
        return user


    def get_user_info(self, email: str) -> dict:
        sql = text("SELECT * FROM Users WHERE email = :email")
        user = self.session.execute(sql, {"email": email}).one_or_none()

        if not user:
            raise self._construct_email_not_found(email) # technically this shouldn't ever happen (?)
        
        return user._asdict()
        
    
    def update_session_token(self, user_id: int, token: str) -> int: # remove most likely, web tokens handled via JWT
        # Check if user exists, will raise exception otherwise.
        self.unique_id_exists(user_id)
        
        sql = """
            UPDATE Users 
            SET token = %s 
            WHERE id = %s
            RETURNING token
        """
        
        result = self.session.execute(text(sql), {"token": token, "id": user_id}).scalar_one_or_none()
        if not result:
            raise RepositoryInternalError(
                caller_name=self.__class__.__name__,
                message=f"An error occurred updating session token, 0 changes made!",
                show_error=False
            )

        return result
        
        
    def get_authenticated_user(self, email: str, token: str, return_info="*") -> dict: # remove most likely, web tokens handled via JWT
        sql = text("SELECT :ret FROM Users WHERE email = :email AND token = :token")
        
        result = self.session.execute(sql, {"ret": return_info, "email": email, "token": token}).one_or_none()
        if not result:
            raise self._construct_email_not_found(email)
        
        return result._asdict()
        
    
    def update_account_status(self, email: str, new_role: int) -> int:
        # Check if user exists, will raise exception otherwise
        self.unique_email_exists(email)
        
        sql = """
            "UPDATE Users 
            SET acc_status = :role 
            WHERE email = :email
            RETURNING acc_status
        """
        
        result = self.session.execute(text(sql), {"role": new_role, "email": email}).scalar_one_or_none()
        if not result:
            raise RepositoryInternalError(
                self.__class__.__name__,
                message="An error occurred updating account status, 0 changes made!",
                show_error=True
            )
        
        return result
        
    
    def update_user_password(self, user_id: int, hashed_password: str) -> int:
        # Check if user exists, will raise exception otherwise.
        self.unique_id_exists(user_id)
        
        sql = """
            UPDATE Users 
            SET passwd = :passwd_hash 
            WHERE id = :user_id
            RETURNING id
        """
        
        result = self.session.execute(
            text(sql), 
            {"passwd_hash": hashed_password, "user_id": user_id}
        ).scalar_one_or_none()
        
        if not result:
            raise RepositoryInternalError(
                self.__class__.__name__,
                message="An error occurred updating password, 0 changes made!",
                show_error=True
            )
        
        return result

    
    def update_user_times(self, user_id: int, start_time: str, end_time: str) -> tuple[str, str]:
        # Check if user exists, will raise exception otherwise.
        self.unique_id_exists(user_id)
        
        sql = """
            UPDATE Users
            SET starting_time = %(start_time)s, ending_time = %(ending_time)s
            WHERE id = %(uid)s
            RETURNING starting_time, ending_time
        """
        args = {
            "start_time": start_time,
            "ending_time": end_time,
            "uid": user_id,
        }
        
        result = self.session.execute(text(sql), args).scalars()
        if result != 2:
            raise RepositoryInternalError(
                self.__class__.__name__,
                message="An error occurred updating user times, 0 changes made!",
                show_error=True
            )
        
        return result[0], result[1]


    # below is related to userpreferencesapi.py, they get user_id many different ways lol
    def get_user_start_and_end_times(self, user_id: int) -> tuple[int, int]:
        sql = text("SELECT starting_time, ending_time FROM Users WHERE id = :user_id")
        args = {"user_id": user_id}
        
        user_times = self.session.execute(sql, args).scalars()

        if user_times != 2: # Incorrectly sized results
            raise self._construct_id_not_found(user_id)

        return user_times[0], user_times[1]


    def get_user_id_from_jwt_and_email(self, email:str, token: str) -> int: # remove maybe as we don't need to store jwt in db (same reasoning as above)
        sql = text("SELECT id FROM Users WHERE email = :email AND token = :token")
        args = {"email": email, "token": token}
        
        result = self.session.execute(sql, args).scalar_one_or_none()
        if not result:
            raise RepositoryNotFoundError(
                caller_name=self.__class__.__name__,
                message=f"A user with an email = {email} could not be found with provided token!",
                show_error=False
            )
        
        return result


    def get_station_id_from_user_preferences(self, user_id: int) -> ScalarResult[Any]:
        # Check if a single user with provided id exists, otherwise raise exception
        self.unique_id_exists(user_id)
        
        sql = text("SELECT station_id FROM UserPreferences WHERE user_id = :user_id")
        args = {"user_id": user_id}
        
        return self.session.execute(sql, args).scalars()


    def delete_user_preferences(self, user_id: int) -> ScalarResult[Any]:
        sql = """
            DELETE FROM UserPreferences
            WHERE user_id = :user_id
            RETURNING station_id
        """
        args = {"user_id": user_id}
        
        return self.session.execute(text(sql), args).scalars()

    def create_user_station_preference(self, user_id: int, station_id: int):
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
                show_error=True
            )



    def create_user_reset_token(self, user_id, hashed_token):
        """
        TODO: Move helpers like this function and the ones below somewhere else
        """
        sql = """
            INSERT INTO reset_requests (uid, token, expiration) 
            VALUES (:user_id, :token_hash, NOW() + INTERVAL '1 hour');
            RETURNING id
        """
        args = {"user_id": user_id, "token_hash": hashed_token}
                
        result = self.session.execute(text(sql), args).scalar_one_or_none()
        if not result:
            raise RepositoryInternalError(
                self.__class__.__name__,
                message="An error occurred creating new reset token, no token created!",
                show_error=False
            )

# the two methods below may need to be rewritten as I don't see the purpose of storing token hashes especially as we need to refresh the JWT to avoid fast auto logouts...

    def get_user_id_from_valid_reset_request_token(self, token_hash) -> int | None:
        """
        look into later
        """
        sql = """
            SELECT u.id FROM reset_requests as r
            INNER JOIN Users AS u ON r.uid = u.id
            WHERE r.token = :token_hash AND r.expiration >= NOW();
        """
        return self.session.execute(text(sql), {"token_hash": token_hash}).scalar_one_or_none()

    
    def delete_user_id_from_reset_requests(self, user_id: int):
        sql = "DELETE FROM reset_requests WHERE uid = :user_id RETURNING id;"
        self.session.execute(text(sql), {"user_id": user_id})