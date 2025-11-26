from abc import ABC, abstractmethod
from argparse import Namespace

from flask import Response

import database.src.api.strategy.record_types as record_types
import database.src.db.generic_record_db as generic_db


class Record_API_Strategy(ABC):
    def __init__(self, table_name: str):
        self.table_name = table_name
        
    @abstractmethod
    def get_train_history(self, id: int, page: int, results_num: int) -> Response:
        pass
    
    @abstractmethod
    def post_train_history(self, args: Namespace, datetime_str: str):
        pass
    
    def check_recent_notification(self, unit_addr: str, station_id: int) -> bool:
        return generic_db.check_recent_trains(self.table_name, unit_addr, station_id)
    
    def add_new_pin(self, unit_addr: str):
        self.attempt_auto_fill(unit_addr)
        
        resp_id = generic_db.get_newest_record_id(self.table_name, unit_addr)
        result = generic_db.add_new_pin(self.table_name, resp_id, unit_addr)
        
    def attempt_auto_fill(self, unit_addr: str):
        symb = generic_db.check_for_record_field(self.table_name, unit_addr, "symbol_id")
        engi = generic_db.check_for_record_field(self.table_name, unit_addr, "engine_num")
        record_id = generic_db.get_newest_record_id(self.table_name, unit_addr)
        
        if symb:
            resp = generic_db.update_record_field(self.table_name, record_id, symb, "symbol_id")
            
        if engi:
            resp = generic_db.update_record_field(self.table_name, unit_addr, engi, "engine_num")
        else:
            print("No engine number to update!")