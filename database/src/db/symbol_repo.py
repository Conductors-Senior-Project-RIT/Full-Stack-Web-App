"""
Symbols database layer 

This module handles all database CRUD operations for Symbol records
"""

from typing import NoReturn, Optional, Any

from psycopg import Error, OperationalError
from record_types import RecordTypes
from trackSense_db_commands import run_get_cmd, run_exec_cmd
from database_status import *


def get_symbol_name(id: int) -> str:
    """
    TODO: integrate this function to replace sql queries in train_history.py's def get_eot() 
    Returns symbol name for train given an id
    "id": The id of a train record to retrieve.
    """

    try:
        sql = "SELECT symb_name FROM Symbols WHERE id = %(symid)s"
        named_args = {"symid": id}

        return run_get_cmd(sql, named_args)[0]
    
    except OperationalError:
        raise RepositoryTimeoutError()
    except Error as e:
        raise RepositoryInternalError(f"Could not retrieve symbol name for ({id}): {e}")
    except IndexError as e:
        raise RepositoryParsingError(f"Could not parse symbol ID result: {e}")
    


def get_symbol_names() -> list | None:
    """Retrieves all symbol names stored in the Symbols table.
    
    Returns:
        (list | None): All list of symbol names as strings if the database retrieval was successful; otherwise, None if an error occured.
    """
    # Databse query to retrieve all symbol names in the Symbols table
    sql = """
        SELECT symb_name FROM Symbols
    """

    # Attempt to retrieve and parse a list of symbol names in the database
    try:
        resp = run_get_cmd(sql)
        ret_val = [
            tup[0] for tup in resp
        ]  # run_get_cmd() returns a list of tuples, doing this gives us an array of symbols.
        
        return ret_val
    
    # If an index error occurs while parsing, print that an index error occurred and return None
    except OperationalError:
        raise RepositoryTimeoutError()
    except Error as e:
        raise RepositoryInternalError(f"Could not retrieve symbol names: {e}")
    except IndexError as e:
        raise RepositoryParsingError(f"Could not parse symbol results: {e}")
    
    
def get_symbol_id(symbol_name: str) -> int | None:
    """Retrieves a symbol ID given the name of a symbol from the Symbols table.
    
    Args:
        symbol_name (str): The name of the symbol in the database.
    
    Returns:
        (int | None): The ID of the symbol as an int if the database retrieval was successful; otherwise, None if an error occurred.
    """
    # Databse query to retrieve the symbol names in a list that match the given parameter
    sql = """
        SELECT id FROM Symbols
        WHERE symb_name = %(name)s
    """

    # Try to retrieve the first ID from the resulting tuple list
    try:
        symbol_id = run_get_cmd(sql, args={"name": symbol_name})[0][0]  # Variable assigned if further debugging is implemented
        return symbol_id
    
    # Otherwise, we encountered an error while retrieving
    except OperationalError:
        raise RepositoryTimeoutError()
    except Error as e:
        raise RepositoryInternalError(f"Could not retrieve symbol ID for {symbol_name}: {e}")
    except IndexError as e:
        raise RepositoryParsingError(f"Could not parse resulting symbol name: {e}")
    
    
def insert_new_symbol(symbol_name: str):
    """Inserts a new symbol row into the Symbols table.
    
    Args:
        symbol_name (str): The name of the symbol to create in the database.
        
    Returns:
        (bool): True if the insertion was successful; otherwise, False if an error occurred.
    """
    # Database query to insert a new symbol row into the Symbols table
    sql = """
        INSERT INTO Symbols (symb_name) VALUES
        (%(name)s)
    """
    
    # Attempt to insert the new symbol into the Symbols table
    try:
        run_exec_cmd(sql, args={"name": symbol_name})
    # If an exception occurs, raise a repository layer exception
    except OperationalError:
        raise RepositoryTimeoutError()
    except Error as e:
        raise RepositoryInternalError(f"Could not retrieve symbol ID for {symbol_name}: {e}")
    

