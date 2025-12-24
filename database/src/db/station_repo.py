from psycopg import Error
from database_status import NotFoundError, RepositoryError
from trackSense_db_commands import run_get_cmd, run_exec_cmd

def get_stations() -> list[tuple[int, str]] | None:
    """Returns a collection of ID and station name pairs from the Stations table.

    Returns:
        (list[tuple[int,str]] | None): Will return a list of tuples that contain station IDs and names if operation was successful,
        otherwise, None is returned.
    """
    # Attempt to retrieve and parse a collection of station ID and name pairs.
    try:
        results = run_get_cmd("SELECT id, station_name FROM Stations")
        return [{
            "id": pair[0],
            "name": pair[1]
        } for pair in results]
    
    # If a database error or another error occurs, print the error and return None
    except Error as e:
        raise RepositoryError(f"Could not retrieve station ID and name pairs: {e}")
    except (ValueError, IndexError) as e:
        raise RepositoryError(f"Could not parse station ID and name pairs: {e}")
        

def create_new_station(station_name: str, hashed_password: str):
    """Creates a new station given a station name and a hashed password in the Stations table.
    
    Args:
        station_name (str): The name of a new station.
        hashed_password (str): A hashed password for the new station.
        
    Returns:
        bool: Returns True if the station was created without error; otherwise, return False if an error occurred.
    """
    # Attempt to create a new station and return True if successful.
    try:
        sql = """
            INSERT INTO Stations (station_name, passwd) VALUES
            (%(station_name)s, %(passwd)s)
        """
        result = run_exec_cmd(sql, args={"station_name": station_name, "passwd": hashed_password})
        if result == 0:
            raise RepositoryError(f"Could not create a new station, 0 rows created.")

    except Error as e:
        raise RepositoryError(f"Could not create a new station: {e}")  

def update_station_password(station_id: str, hashed_password: str) -> str:
    """Updates a station's password given its respective ID.
    
    Args:
        station_name (str): The ID of the station to update.
        hashed_password (str): The new hashed password for the station.
    """
    # Attempt to update a station's password and return True if successful.
    try:
        sql = """
            UPDATE Stations
            SET passwd = %(hashed_pw)s
            WHERE id = %(id)s
        """
        result = run_exec_cmd(sql, args={"hashed_pw": hashed_password, "id": station_id})
        if result == 0:
            raise NotFoundError("Station could not be found!")
        
    # If a database error or another error occurs, print the error and return False
    except Error as e:
        raise RepositoryError(f"Could not update a station: {e}")  

def get_station_id(station_name: str | None ) -> int | None:
    """Returns the ID of a station given its name.

    Args:
        station_name (str): The name of the station.

    Returns:
        str: The ID of the station given its name.
    """
    try:
        sql = "SELECT id FROM Stations WHERE station_name = %(station_name)s)"
        results = run_get_cmd(sql, args={"station_name": station_name})
        if not results:
            return None

        return results[0][0]
    except Error as e:
        print(f"A database error occurred while retrieving a station id from a station name: {e}")
        return None