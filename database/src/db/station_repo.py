from datetime import date
from typing import Any

from psycopg import Error, OperationalError
from database.src.db.database_core import *
from trackSense_db_commands import run_get_cmd, run_exec_cmd

class StationRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session)
        

    @repository_error_handler
    def get_stations(self) -> list[dict[str, Any]]:
        """Returns a collection of ID and station name pairs from the Stations table.

        Returns:
            (list[tuple[int,str]] | None): Will return a list of tuples that contain station IDs and names if operation was successful,
            otherwise, None is returned.
        """
        # Attempt to retrieve and parse a collection of station ID and name pairs.
        results = run_get_cmd("SELECT id, station_name FROM Stations")
        return [{
            "id": pair[0],
            "name": pair[1]
        } for pair in results]
    
            
    @repository_error_handler
    def create_new_station(self, station_name: str, hashed_password: str):
        """Creates a new station given a station name and a hashed password in the Stations table.
        
        Args:
            station_name (str): The name of a new station.
            hashed_password (str): A hashed password for the new station.
            
        Returns:
            bool: Returns True if the station was created without error; otherwise, return False if an error occurred.
        """
        # Attempt to create a new station and return True if successful.
        sql = """
            INSERT INTO Stations (station_name, passwd) VALUES
            (%(station_name)s, %(passwd)s)
        """
        result = run_exec_cmd(sql, args={"station_name": station_name, "passwd": hashed_password})
        if result == 0:
            raise RepositoryInternalError(f"Could not create a new station, 0 rows created.")


    @repository_error_handler
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
        """
        result = run_exec_cmd(sql, args={"hashed_pw": hashed_password, "id": station_id})
        if result == 0:
            raise RepositoryNotFoundError(station_id)
            

    def get_station_id(self, station_name: str) -> int:
        """Returns the ID of a station given its name.

        Args:
            station_name (str): The name of the station.

        Returns:
            str: The ID of the station given its name.
        """
        try:
            sql = "SELECT id FROM Stations WHERE station_name = %(station_name)s"
            results = run_get_cmd(sql, args={"station_name": station_name})
            if len(results) < 1:
                raise RepositoryNotFoundError(station_name)
            return results[0][0]
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not retrieve a station id for {station_name}: {e}"
            )
        

    @repository_error_handler
    def get_last_seen(self, station_name: str) -> str:
        sql = "SELECT last_seen FROM stations WHERE station_name = %s;"
        results = run_get_cmd(sql, (station_name,))
        
        if len(results) == 0:
            raise RepositoryNotFoundError(station_name)
        
        seen_date = results[0][0]
        formatted_date = seen_date.strftime("%I:%M %p") if seen_date.date() == date.today() \
            else seen_date.strftime("%b %d, %Y at %I:%M %p")
            
        return formatted_date

        
    @repository_error_handler
    def update_last_seen(self, station_id: int):
        sql = "UPDATE stations SET last_seen = NOW() WHERE id = %s;"
        result = run_exec_cmd(sql, (station_id,))
        
        if result == 0:
            raise RepositoryNotFoundError(station_id)
        
