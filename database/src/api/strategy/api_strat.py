from abc import ABC, abstractmethod
from argparse import Namespace
from typing import Any

from flask import Response, jsonify

import database.src.api.strategy.record_types as record_types
import database.src.db.generic_record_db as generic_db
from db.trackSense_db_commands import run_get_cmd


class Record_API_Strategy(ABC):
    def __init__(self, table_name: str):
        self._table_name = table_name
        
    # ---- TRAIN HISTORY ---- #
    @abstractmethod
    def get_train_history(self, id: int, page: int, results_num: int) -> Response:
        pass
    
    @abstractmethod
    def post_train_history(self, args: Namespace, datetime_str: str):
        pass

    @abstractmethod
    def parse_station_records(self, station_records: list[tuple[Any, ...]]) -> list[dict[str, Any]] | None:
        """EOT and HOT station records parsed differently
        """
        pass

    def check_recent_notification(self, unit_addr: str, station_id: int) -> bool:
        return generic_db.check_recent_trains(self._table_name, unit_addr, station_id)
    
    def add_new_pin(self, unit_addr: str):
        self.attempt_auto_fill(unit_addr)
        
        resp_id = generic_db.get_newest_record_id(self._table_name, unit_addr)
        result = generic_db.add_new_pin(self._table_name, resp_id, unit_addr)
        
    def attempt_auto_fill(self, unit_addr: str):
        symb = generic_db.check_for_record_field(self._table_name, unit_addr, "symbol_id")
        engi = generic_db.check_for_record_field(self._table_name, unit_addr, "engine_num")
        record_id = generic_db.get_newest_record_id(self._table_name, unit_addr)
        
        if symb:
            resp = generic_db.update_record_field(self._table_name, record_id, symb, "symbol_id")
            
        if engi:
            resp = generic_db.update_record_field(self._table_name, unit_addr, engi, "engine_num")
        else:
            print("No engine number to update!")

    # ---- STATION HANDLER ---- #
    def get_station_records(self, station_id: int | None) -> list[dict[str, Any]] | None:
        """Template Method design pattern to deal with generalization/ code dupe (very similar database accessing logic)
        Get EOT & HOT records from specified station

        todo: left off at needing to finish: get_most_recent_station_records(), there's some overlap in code there so need to review
        """
        # This should never happen
        if station_id is None:
            raise ValueError("Invalid station ID provided!")
        
        station_records = generic_db.get_records_for_station(self._table_name, station_id)
        if not station_records:
            return None
        return self.parse_station_records(station_records)
    
    # ---- RECORD COLLATION ---- #
    @abstractmethod
    def get_record_collation(self, page: int) -> dict[str, Any]:
        pass
    
    # ---- RECORD VERIFICATION ---- #
    @abstractmethod
    def get_unverified_records(self, page: int) -> dict[str, Any]:
        pass
        