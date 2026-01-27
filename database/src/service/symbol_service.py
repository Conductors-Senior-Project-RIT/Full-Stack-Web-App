from typing import Any
from service_core import BaseService
from db.database_status import *
from service_core import *
import db.symbol_repo as repo


class SymbolService(BaseService):
    def __init__(self):
        super().__init__("Symbol")
        
    
    def get_symbol(self, symbol_name: str) -> list[str] | list[int]:
        try:
            if symbol_name is None:
                return repo.get_symbol_names()
            else:
                return [repo.get_symbol_id(symbol_name)]
                
        except RepositoryTimeoutError:
            raise ServiceTimeoutError(self)
        except (RepositoryInternalError, RepositoryParsingError) as e:
            raise ServiceInternalError(self, str(e))
        
        
    def create_symbol(self, symbol_name: str):
        try:
            repo.insert_new_symbol(symbol_name)
        except RepositoryTimeoutError:
            raise ServiceTimeoutError()
        except RepositoryInternalError as e:
            raise ServiceInternalError(str(e))
        