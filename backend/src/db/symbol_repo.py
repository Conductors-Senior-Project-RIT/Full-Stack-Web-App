"""
Symbols database layer 

This module handles all database CRUD operations for Symbol records
"""
from typing import Any
from sqlalchemy import text, ScalarResult

from .db_core.models import Symbol
from .db_core.repository import BaseRepository
from .db_core.exceptions import RepositoryNotFoundError, repository_error_translator, \
    repository_error_handler

class SymbolRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(Symbol, session)


    def get_symbol_name(self, id: int) -> str:
        """
        TODO: integrate this function to replace sql queries in train_history.py's def get_eot() 
        Returns symbol name for train given an id
        "id": The id of a train record to retrieve.
        """

        try:
            sql = "SELECT symb_name FROM Symbols WHERE id = :sym_id"
            args = {"sym_id": id}
            
            result = self.session.execute(text(sql), args).scalar_one_or_none()
            
            if not result:
                raise RepositoryNotFoundError(
                    caller_name=self.__class__.__name__,
                    message=f"Symbol with ID = {id}, could not be found!",
                    show_error=False
                )

            return result
        
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not retrieve symbol name for ({id}): {e}"
            )
        

    @repository_error_handler
    def get_symbol_names(self) -> ScalarResult[Any]:
        """Retrieves all symbol names stored in the Symbols table.
        
        Returns:
            (list): All list of symbol names as strings if the database retrieval was successful.
        """
        # Database query to retrieve all symbol names in the Symbols table
        sql = "SELECT symb_name FROM Symbols"
        # Attempt to retrieve and parse a list of symbol names in the database
        return self.session.execute(text(sql)).scalars()


        
        
    def get_symbol_id(self, symbol_name: str) -> int | None:
        """Retrieves a symbol ID given the name of a symbol from the Symbols table.
        
        Args:
            symbol_name (str): The name of the symbol in the database.
        
        Returns:
            (int | None): The ID of the symbol as an int if the database retrieval was successful; otherwise, None if an error occurred.
        """
        # Databse query to retrieve the symbol names in a list that match the given parameter
        sql = "SELECT id FROM Symbols WHERE symb_name = :name"

        # Try to retrieve the first ID from the resulting tuple list
        try:
            symbol_id = self.session.execute(text(sql), {"name": symbol_name}).scalar_one_or_none()
            
            if symbol_id is None:
                raise RepositoryNotFoundError(
                    caller_name=self.__class__.__name__,
                    message=f"Could not find symbol with name = {symbol_name}",
                    show_error=False
                )
        
        # Otherwise, we encountered an error while retrieving
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not retrieve symbol ID for {symbol_name}: {e}"
            )
        
    
    def insert_new_symbol(self, symbol_name: str):
        """Inserts a new symbol row into the Symbols table.
        
        Args:
            symbol_name (str): The name of the symbol to create in the database.
            
        Returns:
            (bool): True if the insertion was successful; otherwise, False if an error occurred.
        """
        # Database query to insert a new symbol row into the Symbols table
        sql = """
            INSERT INTO Symbols (symb_name) 
            VALUES (:name)
            RETURNING id
        """
        
        # Attempt to insert the new symbol into the Symbols table
        try:
            return self.session.execute(text(sql), {"name": symbol_name}).scalar_one()
            
        # If an exception occurs, raise a repository layer exception
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not retrieve symbol ID for {symbol_name}: {e}"
            )
