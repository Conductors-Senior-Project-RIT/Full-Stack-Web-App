from datetime import datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from .db_core.exceptions import RepositoryErrorHandler as RHandler
from .db_core.exceptions import RError as E
from .db_core.models import Station
from .db_core.repository import BaseRepository


class StationRepository(BaseRepository[Station]):
    """A database interface for querying station records.

    This class inherits the generic CRUD functionality defined in 
    [`BaseRepository`][...db_core.repository.BaseRepository] that may be useful for simple 
    operations. This class contains concrete methods which execute queries beyond simple CRUD 
    operations using the [`Station`][...db_core.models.Station] model.
    """
    
    def __init__(self, session: Session):
        """Constructor for a repository that interacts with the 
        [`Station`][....db_core.models.Station] model.

        Args:
            session (Session): Specifies the database session the repository operates
                in. All functions in this class flushes all changes to the session. It
                is the job of higher layers to commit or rollback any changes.
        """
        super().__init__(Station, session)
        

    @RHandler.layer_error_decorator()
    def get_stations(self) -> list[dict[str, Any]]:
        """Returns a collection of ID and station name pairs.

        Returns:
            (list[dict[str, Any]]): A list of dictionaries containing `id` and `station_name`
                for each station.
        """
        # Attempt to retrieve and parse all station ID and name pairs.
        stmt = select(self.model.id, self.model.station_name)
        results = self.session.execute(stmt).all()
        
        # Convert the result to a list of dictionaries
        return self.objs_to_dicts(results)
    
            
    @RHandler.layer_error_decorator()
    def create_new_station(self, stat_name: str, hashed_password: str) -> int:
        """Creates a new station from `stat_name` and a `hashed_password` in the `Stations`
        table.

        Args:
            stat_name (str): The name of a new station.
            hashed_password (str): A hashed password for the new station.

        Raises:
            RepositoryExistingRowError: Raised if a station with the same name already
                exists.

        Returns:
            (int): Returns the id of the new station created
        """
        # Check to see if station name exists
        stmt = select(self.model.id).where(self.model.station_name == stat_name)
        result = self.session.execute(stmt).scalar_one_or_none()
        
        self._validate(
            condition=result is None, 
            error_class=E.EXISTING, 
            message=f"A station with the name {stat_name} already exists!", 
            show_error=True
        )
        
        # Add a new station instance to the session
        new_station = self.model(
            station_name = stat_name, 
            passwd = hashed_password
        )
        self.session.add(new_station)
        self.session.flush()
        return new_station.id



    @RHandler.layer_error_decorator()
    def update_station_password(self, station_id: int, hashed_password: str) -> str:
        """Updates a station's password with `hashed_password` if a matching `station_id`
        exists.

        Args:
            station_id (int): The ID of the station to update.
            hashed_password (str): The new hashed password for the station.

        Raises:
            RepositoryNotFoundError: Raised if a station with `station_id` does not exist.
            RepositoryInvalidArgumentError: Raised if either argument is of the incorrect
                type.

        Returns:
            (str): The newly updated password from the database session.
        """
        return self._update_station_value(station_id, "passwd", hashed_password)
    
    
    def update_station_name(self, station_id: int, new_name: str) -> str:
        """Updates a station's name with `new_name` if a matching `station_id` exists.

        Args:
            station_id (int): The ID of the station to update.
            new_name (str): The new name for the station.

        Raises:
            RepositoryNotFoundError: Raised if a station with `station_id` does not exist.
            RepositoryInvalidArgumentError: Raised if either argument is of the incorrect
                type.

        Returns:
            (str): The newly updated name from the database session.
        """
        return self._update_station_value(station_id, "station_name", new_name)
    
    
    def _update_station_value(self, station_id: int, station_field: str, new_value: Any) -> float:
        """Updates a station's column with a new value if a matching `station_id` exists.

        Args:
            station_id (int): The ID of the station to update.
            station_field (str): The name of the column to update.
            new_value (Any): The new value for the station's respective column.

        Raises:
            RepositoryNotFoundError: Raised if a station with `station_id` does not exist.
            RepositoryInvalidArgumentError: Raised if either argument is of the incorrect
                type.

        Returns:
            (float): The newly updated value from the database session.
        """
        self._validate(
            condition=isinstance(station_id, int) and isinstance(station_field, str), 
            error_class=E.INVALID_ARG, 
            message=f"Invalid argument types provided when updating: {station_field}!"
        )

        # Will raise a RepositoryNotFoundError if station does not exist
        result = self.update_with_pk(station_id, {station_field: new_value}, to_dict=False)
        return getattr(result, station_field)


    def get_station_id(self, stat_name: str) -> int:
        """Returns the ID of a station with a matching station name.

        Args:
            stat_name (str): The name of the station.

        Raises:
            RepositoryNotFoundError: Raised if a station with `stat_name` 
                does not exist.

        Returns:
            (str): The ID of the station.
        """
        try:
            # Select the station ID where the station name matches the provided name.
            stmt = select(self.model.id).where(self.model.station_name == stat_name)
            result = self.session.execute(stmt).scalar_one_or_none()
            
            # If None, then a record was likely not found.
            self._validate(
                condition=result is not None, 
                error_class=E.NOT_FOUND, 
                message=f"Could not find {stat_name}!", 
                show_error=True
            )
            
            return result
        
        # Handle any errors that may occur, including the station name in the error message.
        except Exception as e:
            raise self._translate_and_raise(e, f"Could not retrieve a station id for {stat_name}!")
        

    @RHandler.layer_error_decorator()
    def get_last_seen(self, station_name: str) -> datetime:
        """Returns a datetime instance of the station's last seen timestamp.

        Args:
            station_name (str): The name of the station to retrieve from.

        Raises:
            RepositoryNotFoundError: Raised if a station is not found.

        Returns:
            (datetime): A datetime instance of a station's last seen timestamp.
        """
        # Get the last seen field from a station's corresponding name
        stmt = select(self.model.last_seen).where(self.model.station_name == station_name)
        result = self.session.execute(stmt).scalar_one_or_none()
        
        # If result is None, it was likely not found
        self._validate(result is not None, E.NOT_FOUND, f"Could not find {station_name}!", True)
        
        # Format the seen date based on whether it was seen today    
        return result

        
    @RHandler.layer_error_decorator()
    def update_last_seen(self, station_id: int) -> datetime:
        """Updates a station's last seen timestamp to the current time 
        during execution.

        Args:
            station_id (int): The ID of the station to update.

        Raises:
            RepositoryNotFoundError: Raised if a station is not found.

        Returns:
            (datetime): A timestamp of the result.
        """
        # Update a station's last seen to the current timestamp, returning the new value
        # Probably can use ORM-style like update_station_password, but func.now() matches timezone in db
        stmt = (
            update(self.model)
            .values(last_seen = func.now())
            .where(self.model.id == station_id)
            .returning(self.model.last_seen)
        )

        result = self.session.execute(stmt).scalar_one_or_none()

        # If None is returned, the station was likely not found
        self._validate(
            condition=result is not None, 
            error_class=E.NOT_FOUND, 
            message=f"Could not find station with id: {station_id}!", 
            show_error=True
        )
            
        return result
