from typing import Any
from service_core import BaseService
from database.src.db.database_core import *
from service_core import *
from db.symbol_repo import SymbolRepository


class SymbolService(BaseService):
    def __init__(self, session):
        self.repo = SymbolRepository(session)
        super().__init__("Symbol")
        
    
    def get_symbol(self, symbol_name: str) -> list[str] | list[int]:
        try:
            if symbol_name is None:
                return self.repo.get_symbol_names()
            else:
                return [self.repo.get_symbol_id(symbol_name)]
                
        except RepositoryTimeoutError:
            raise ServiceTimeoutError(self)
        except (RepositoryInternalError, RepositoryParsingError) as e:
            raise ServiceInternalError(self, str(e))
        
        
    def create_symbol(self, symbol_name: str):
        try:
            self.repo.insert_new_symbol(symbol_name)
        except RepositoryTimeoutError:
            raise ServiceTimeoutError()
        except RepositoryInternalError as e:
            raise ServiceInternalError(str(e))
        