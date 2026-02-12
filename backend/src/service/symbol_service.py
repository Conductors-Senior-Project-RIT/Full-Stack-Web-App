from typing import Any
from service_core import BaseService
from backend.src.db.database_core import *
from service_core import *
from db.symbol_repo import SymbolRepository


class SymbolService(BaseService):
    def __init__(self, session):
        self._symbol_repo = SymbolRepository(session)
        super().__init__()
        
    
    def get_symbol(self, symbol_name: str) -> list[str] | list[int]:
        if symbol_name is None:
            return self._symbol_repo.get_symbol_names()
        else:
            return [self._symbol_repo.get_symbol_id(symbol_name)]
        
        
    def create_symbol(self, symbol_name: str):
        self._symbol_repo.insert_new_symbol(symbol_name)
        