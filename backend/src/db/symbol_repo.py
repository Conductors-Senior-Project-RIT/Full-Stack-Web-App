import sys
from sqlalchemy import select

from .db_core.models import Symbol
from .db_core.repository import BaseRepository
from .db_core.exceptions import (
    RepositoryExistingRowError,
    RepositoryNotFoundError,
    repository_error_translator,
    repository_error_handler,
)


class SymbolRepository(BaseRepository):
    """A database interface for querying symbol records.

    This class inherits the generic CRUD functionality defined in `BaseRepository` 
    that may be useful for simple operations. This class contains concrete methods 
    which execute functionality using the `Symbol` model.
    """
    def __init__(self, session):
        """Constructor for a repository that interacts with symbol records. 
        References a database session that is used by all queries.
        
        Args:
            session (Session): Specifies the database session the repository operates
                in. All functions in this class flushes all changes to the session. It
                is the job of higher layers to commit or rollback any changes.
        """
        super().__init__(Symbol, session)

    def get_symbol_name(self, id: int) -> str:
        """Returns the name of a symbol when provided with its corresponding ID.

        Args:
            id (int): ID of a symbol.

        Returns:
            str: A corresponding symbol name.
            
        Raises:
            `RepositoryNotFoundError`: Raised if a symbol row is not found with the
                    provided ID.
            `RepositoryError`: Raised if any other errors occurs (SQLAlchemy or
                    psycopg2).
        """

        try:
            stmt = select(self.model.symb_name).where(self.model.id == id)
            result = self.session.execute(stmt).scalar_one_or_none()

            if not result:
                raise RepositoryNotFoundError(
                    self.__class__.__name__,
                    sys._getframe().f_code.co_name,
                    f"Symbol with ID = {id}, could not be found!",
                    False,
                )

            return result

        except Exception as e:
            raise repository_error_translator(
                e,
                self.__class__.__name__,
                sys._getframe().f_code.co_name,
                f"Could not retrieve symbol name for ({id}): {e}",
            )

    @repository_error_handler()
    def get_symbol_names(self) -> list[str]:
        """Retrieves all symbol names stored in the database.

        Returns:
            (list): All list of symbol names as strings if the database retrieval was
                successful.
                
        Raises:
            `RepositoryError`: Raised if any errors occur (SQLAlchemy or psycopg2).
        """
        return list(self.session.execute(select(self.model.symb_name)).scalars().all())

    def get_symbol_id(self, symbol_name: str) -> int:
        """Retrieves a symbol ID given the name of a symbol from the database.

        Args:
            symbol_name (str): The name of the symbol in the database.

        Returns:
            (int): The ID of the symbol as an int if the database retrieval was
                successful.
                
        Raises:
            `RepositoryNotFoundError`: Raised if a symbol row is not found with the
                    provided name.
            `RepositoryError`: Raised if any other errors occurs (SQLAlchemy or
                    psycopg2).
        """
        try:
            sql = select(self.model.id).where(self.model.symb_name == symbol_name)
            symbol_id = self.session.execute(sql).scalar_one_or_none()

            if symbol_id is None:
                raise RepositoryNotFoundError(
                    self.__class__.__name__,
                    sys._getframe().f_code.co_name,
                    f"Could not find symbol with name = {symbol_name}",
                    False,
                )

            return symbol_id

        # Encountered an error while retrieving
        except Exception as e:
            raise repository_error_translator(
                e,
                self.__class__.__name__,
                sys._getframe().f_code.co_name,
                f"Could not retrieve symbol ID for {symbol_name}: {e}",
            )

    def insert_new_symbol(self, symbol_name: str) -> int:
        """Creates a new symbol in the database.

        Args:
            symbol_name (str): The name of the symbol to create in the database.

        Returns:
            (int): The ID of the newly created symbol.

        Raises:
            `RepositoryExistingRowError`: Raised if a symbol with the same name already exists.
            `RepositoryError`: Raised if any other errors occur (SQLAlchemy or psycopg2).
        """
        try:
            # Check to see if symbol name exists
            stmt = select(self.model.id).where(self.model.symb_name == symbol_name)
            result = self.session.execute(stmt).scalar_one_or_none()

            if result is not None:
                raise RepositoryExistingRowError(
                    self.__class__.__name__,
                    sys._getframe().f_code.co_name,
                    f"A symbol with the name {symbol_name} already exists!",
                    True,
                )

            # Attempt to insert the new symbol into the Symbols table
            new_symbol = self.model(symb_name=symbol_name)
            self.session.add(new_symbol)
            self.session.flush()
            return new_symbol.id

        # If an exception occurs, raise a repository layer exception
        except Exception as e:
            raise repository_error_translator(
                e,
                self.__class__.__name__,
                sys._getframe().f_code.co_name,
                f"Could not create new symbol '{symbol_name}': {e}",
            )
