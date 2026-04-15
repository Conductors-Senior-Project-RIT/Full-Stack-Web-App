from datetime import date, datetime
from typing import Any
from sqlalchemy import func, insert, select, text, update

from .db_core.models import Station

from .db_core.exceptions import RepositoryNotFoundError, RepositoryInternalError, RepositoryInvalidArgumentError, \
    RepositoryExistingRowError, repository_error_handler, repository_error_translator
from .db_core.repository import BaseRepository

class StationRepository(BaseRepository[Station]):
    def __init__(self, session):
        super().__init__(Station, session)
        

    @repository_error_handler()
    def get_stations(self) -> list[dict[str, Any]]:
        """Returns a collection of ID and station name pairs from the Stations table.

        Returns:
            (list[dict[str, Any]]): Will return a list of tuples that contain station IDs and names if operation was successful.
        """
        # Attempt to retrieve and parse all station ID and name pairs.
        stmt = select(self.model.id, self.model.station_name)
        results = self.session.execute(stmt).all()
        
        # Convert the result to a list of dictionaries
        return self.objs_to_dicts(results)
    
            
    @repository_error_handler()
    def create_new_station(self, stat_name: str, hashed_password: str) -> int:
        """Creates a new station given a station name and a hashed password in the Stations table.
        
        Args:
            station_name (str): The name of a new station.
            hashed_password (str): A hashed password for the new station.
            
        Returns:
            bool: Returns the id of the new station created
        """
        # Check to see if station name exists
        stmt = select(self.model.id).where(self.model.station_name == stat_name)
        result = self.session.execute(stmt).scalar_one_or_none()
        
        if result:
            raise RepositoryExistingRowError(
                caller_name=self.__class__.__class__,
                message=f"A station with the name {stat_name} already exists!",
                show_error=True
            )
        
        # Create the query to insert a new station record, returning the new id
        stmt = (
            insert(self.model)
            .values(
                station_name = stat_name,
                passwd = hashed_password
            )
            .returning(self.model.id)
        )
        
        # Execute the query, and return the id
        result = self.session.execute(stmt).scalar_one_or_none()
        
        # If the returned id is None, something went wrong
        if not result:
            raise RepositoryInternalError(
                caller_name=self.__class__.__name__,
                message=f"Could not create a new station, 0 rows created.",
                show_error=True
            )
        
        return result


    @repository_error_handler()
    def update_station_password(self, station_id: int, hashed_password: str) -> str:
        """Updates a station's password given its respective ID.
        
        Args:
            station_name (int): The ID of the station to update.
            hashed_password (str): The new hashed password for the station.
        """
        if not isinstance(station_id, int) or not isinstance(hashed_password, str):
            raise RepositoryInvalidArgumentError(
                caller_name=self.__class__.__name__,
                message="Either station_id or hashed_password are of the incorrect type!",
                show_error=False
            )
        
        # Will raise a RepositoryNotFoundError if station does not exist
        result = self.update_with_pk(station_id, {"passwd": hashed_password}, to_dict=False)  
        return result.id
            

    def get_station_id(self, stat_name: str) -> int:
        """Returns the ID of a station given its name.

        Args:
            stat_name (str): The name of the station.

        Returns:
            str: The ID of the station given its name.
        """
        try:
            # Select the station ID where the station name matches the provided name.
            stmt = select(self.model.id).where(self.model.station_name == stat_name)
            result = self.session.execute(stmt).scalar_one_or_none()
            
            # If None, then a record was likely not found.
            if not result:
                raise RepositoryNotFoundError(
                    caller_name=self.__class__.__name__, 
                    message=f"Could not find {stat_name}!",
                    show_error=True
                )
            
            return result
        
        # Handle any errors that may occur, including the station name in the error message.
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not retrieve a station id for {stat_name}: {e}"
            )
        

    @repository_error_handler()
    def get_last_seen(self, stat_name: str) -> str:
        """Returns a formatted string of the station's last seen timestamp. 
        If the timestamp occurred today, the string is formatted as: 'HH:MM AM/PM'; 
        otherwise, it is formatted as: 'MON DD, YYYY at HH:MM AM/PM'.

        Args:
            stat_name (str): The name of the station to retrieve from.

        Raises:
            RepositoryNotFoundError: Raised if a station is not found.

        Returns:
            str: A formatted string of a station's last seen timestamp.
        """
        # Get the last seen field from a station's corresponding name
        stmt = select(self.model.last_seen).where(self.model.station_name == stat_name)
        result = self.session.execute(stmt).scalar_one_or_none()
        
        # If result is None, it was likely not found
        if not result:
            raise RepositoryNotFoundError(
                caller_name=self.__class__.__name__, 
                message=f"Could not find {stat_name}!",
                show_error=True
            )
        
        # Format the seen date based on whether it was seen today
        seen_date = result
        formatted_date = seen_date.strftime("%I:%M %p") if seen_date.date() == date.today() \
            else seen_date.strftime("%b %d, %Y at %I:%M %p")
            
        return formatted_date

        
    @repository_error_handler()
    def update_last_seen(self, station_id: int) -> datetime:
        """Updates a station's last seen timestamp to the current time during execution.  
        Returns a datetime object representing the result.

        Args:
            station_id (int): The ID of the station to update.

        Raises:
            RepositoryNotFoundError: Raised if a station is not found.

        Returns:
            datetime: A timestamp of the result.
        """
        # Update a station's last seen to the current timestamp, returning the new value
        stmt = (
            update(self.model)
            .values(last_seen = func.now())
            .where(self.model.id == station_id)
            .returning(self.model.last_seen)
        )

        result = self.session.execute(stmt).scalar_one_or_none()

        # If None is returned, the station was likely not found
        if not result:
            raise RepositoryNotFoundError(
                caller_name=self.__class__.__name__, 
                message=f"Could not find station with id: {station_id}!",
                show_error=True
            )

        return result