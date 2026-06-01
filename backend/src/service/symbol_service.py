from sqlalchemy.orm import Session

from .service_core import BaseService
from ..db.symbol_repo import SymbolRepository


class SymbolService(BaseService):
    """Handles business logic for symbol related data processing. There isn't much
    currently, but might be very useful in the future for symbol operations.
    """
    def __init__(self, session: Session):
        """Initializes a `SymbolRepository` with a provided **SQLAlchemy** session.

        Args:
            session (Session): The SQLAlchemy session to be used for database
                transactions in the service's repository.
        """
        self._symbol_repo = SymbolRepository(session)
        
    def get_symbol(self, symbol_name: str | None) -> list[str] | int:
        """If a symbol name is provided, the ID corresponding to that symbol is returned;
        otherwise, a list of all symbols names in the database are returned.

        Args:
            symbol_name (str | None): The name of a symbol to retrieve. Can be `None` to
                retrieve all symbol names.

        Returns:
            list[str] | int: A list of symbol names or the ID of a specific symbol.
        """
        if symbol_name is None:
            return self._symbol_repo.get_symbol_names()
        else:
            return self._symbol_repo.get_symbol_id(symbol_name)
        
    def create_symbol(self, symbol_name: str) -> int:
        """Creates a new symbol in the database with the provided name.

        A symbol with the same name must not already exist in the database, otherwise an
        error is raised.

        Args:
            symbol_name (str): The name of the new symbol to be created.

        Returns:
            int: The ID of the newly created symbol.
        """
        return self._symbol_repo.insert_new_symbol(symbol_name)
        