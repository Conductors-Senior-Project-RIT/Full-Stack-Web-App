from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any

from backend.src.db.base_record_repo import RecordRepository

R = TypeVar("R", bound=RecordRepository)

class Record_Service_Strategy(Generic[R], ABC):
    def __init__(self, repo: R):
        self.repo: R = repo
        
    # ---- TRAIN HISTORY ---- #
    @abstractmethod
    def get_train_history(self, id: int, page: int, results_num: int):
        pass
    
    @abstractmethod
    def post_train_record(self, args: dict, datetime_str: str):
        pass

    @abstractmethod
    def parse_station_records(self, station_records: list[tuple[Any, ...]]) -> list[dict[str, Any]] | None:
        """EOT and HOT station records parsed differently
        """
        pass

    def check_recent_notification(self, unit_addr: str, station_id: int) -> bool:
        return self.repo.check_recent_trains(unit_addr, station_id)
    
    def add_new_pin(self, unit_addr: str):
        self.attempt_auto_fill(unit_addr)
        
        resp_id = self.repo.get_newest_record_id(unit_addr)
        result = self.repo.add_new_pin(resp_id, unit_addr)
        
    def attempt_auto_fill(self, unit_addr: str):
        symb = self.repo.check_for_record_field(unit_addr, "symbol_id")
        engi = self.repo.check_for_record_field(unit_addr, "engine_num")
        record_id = self.repo.get_newest_record_id(unit_addr)
        
        if symb:
            resp = self.repo.update_record_field(record_id, symb, "symbol_id")
            
        if engi:
            resp = self.repo.update_record_field(unit_addr, engi, "engine_num")
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
        
        station_records = self.repo.get_records_for_station(self._table_name, station_id)
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
        