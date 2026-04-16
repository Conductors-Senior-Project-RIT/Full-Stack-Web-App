from datetime import date
from typing import Any
from sqlalchemy import text

from .db_core.models import Station

from .db_core.exceptions import RepositoryNotFoundError, RepositoryInternalError, \
    repository_error_handler, repository_error_translator
from .db_core.repository import BaseRepository

class StationRepository(BaseRepository[Station]):
    def __init__(self, session):
        super().__init__(Station, session)
        

    @repository_error_handler()
    def get_stations(self) -> list[dict[str, Any]]:
        """Returns a collection of ID and station name pairs from the Stations table.

        Returns:
            (list[tuple[int,str]] | None): Will return a list of tuples that contain station IDs and names if operation was successful,
            otherwise, None is returned.
        """
        # Attempt to retrieve and parse a collection of station ID and name pairs.
        sql = text("SELECT id, station_name FROM Stations")
        results = [row._asdict() for row in self.session.execute(sql).all()]
        
        return [{
            "id": pair["id"],
            "name": pair["station_name"]
        } for pair in results]
    
            
    @repository_error_handler()
    def create_new_station(self, station_name: str, hashed_password: str) -> int:
        """Creates a new station given a station name and a hashed password in the Stations table.
        
        Args:
            station_name (str): The name of a new station.
            hashed_password (str): A hashed password for the new station.
            
        Returns:
            bool: Returns the id of the new station created
        """
        # Attempt to create a new station and return True if successful.
        sql = """
            INSERT INTO Stations (station_name, passwd) 
            VALUES (:station_name, :passwd)
            RETURNING id
        """
        result = self.session.execute(
            text(sql), {"station_name": station_name, "passwd": hashed_password}
        ).scalar_one_or_none()
        
        if not result:
            raise RepositoryInternalError(
                caller_name=self.__class__.__name__,
                message=f"Could not create a new station, 0 rows created.",
                show_error=True
            )
        
        return result


    @repository_error_handler()
    def update_station_password(self, station_id: str, hashed_password: str) -> str:
        """Updates a station's password given its respective ID.
        
        Args:
            station_name (str): The ID of the station to update.
            hashed_password (str): The new hashed password for the station.
        """
        # Attempt to update a station's password and return True if successful.
        sql = """
            UPDATE Stations
            SET passwd = %(hashed_pw)s
            WHERE id = %(id)s
            RETURNING id
        """
        result = self.session.execute(
            text(sql), 
            {"hashed_pw": hashed_password, "id": station_id}
        ).scalar_one_or_none()
        
        if not result:
            raise RepositoryNotFoundError(
                caller_name=self.__class__.__name__, 
                message=f"Could not find station with id: {station_id}!",
                show_error=True
            )
        
        return result
            

    def get_station_id(self, station_name: str) -> int:
        """Returns the ID of a station given its name.

        Args:
            station_name (str): The name of the station.

        Returns:
            str: The ID of the station given its name.
        """
        try:
            sql = "SELECT id FROM Stations WHERE station_name = :station_name"
            result = self.session.execute(text(sql), {"station_name": station_name}).scalar_one_or_none()
            
            if not result:
                raise RepositoryNotFoundError(
                    caller_name=self.__class__.__name__, 
                    message=f"Could not find {station_name}!",
                    show_error=True
                )
            
            return result
        
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not retrieve a station id for {station_name}: {e}"
            )
        

    @repository_error_handler()
    def get_last_seen(self, station_name: str) -> str:
        sql = "SELECT last_seen FROM stations WHERE station_name = :station_name;"
        result = self.session.execute(text(sql), {"station_name": station_name}).scalar_one_or_none()
        
        if not result:
            raise RepositoryNotFoundError(
                caller_name=self.__class__.__name__, 
                message=f"Could not find {station_name}!",
                show_error=True
            )
        
        seen_date = result
        formatted_date = seen_date.strftime("%I:%M %p") if seen_date.date() == date.today() \
            else seen_date.strftime("%b %d, %Y at %I:%M %p")
            
        return formatted_date

        
    @repository_error_handler()
    def update_last_seen(self, station_id: int):
        sql = "UPDATE stations SET last_seen = NOW() WHERE id = %(id)s;"

        result = self.session.execute(
            text(sql),
            {"id": station_id}
        ).scalar_one_or_none()

        if result == 0:
            raise RepositoryNotFoundError(
                caller_name=self.__class__.__name__, 
                message=f"Could not find station with id: {station_id}!",
                show_error=True
            )

        return result