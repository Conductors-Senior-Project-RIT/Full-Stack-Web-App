from typing import Any

from flask import jsonify
from api_strat import Record_Service_Strategy
from database.src.db.hot_repo import HOTRepository, HOTRepositoryError
from database.src.service.service_status import ServiceStatusCode

class HOT_Service_Strategy(Record_Service_Strategy[HOTRepository]):
    def __init__(self):
        super().__init__(HOTRepository())
    
    def get_train_history(self, id: int, page: int, results_num: int):
        try:
            return self.repo.get_train_hot_data(id, page, results_num)
        except HOTRepositoryError as e:
            raise RuntimeError(str(e))
        
    def post_train_record(self, args: dict, datetime_str: str) -> tuple:
        # TODO: Implement better parsing and response handling
        try:
            return self.repo.create_hot_record(args, datetime_str)
        except HOTRepositoryError as e:
            raise RuntimeError(str(e))
        
    
    def add_new_pin(self, unit_addr):
        return super().add_new_pin(unit_addr)
        

    def attempt_auto_fill(self, unit_addr):
        return super().attempt_auto_fill(unit_addr)

    def parse_station_records(self, station_records: list[tuple[Any, ...]]) -> list[dict[str, Any]] | None:
        try:
            hot_records = [
                {
                    "id": record[0],
                    "date_rec": record[1],
                    "frame_sync": record[3],
                    "unit_addr": record[4],
                    "command": record[5],
                    "checkbits": record[6],
                    "parity": record[7],
                }
                for record in station_records
            ]
            return hot_records
        except Exception as e:
            print(f"An error occurred while attempting to parse hot station records: {e}")
            return None
    
    def get_record_collation(self, page: int):
        results = self.repo.get_hot_record_collation(page)
        
        if results is None:
            return jsonify({"error": "Error occured when attempting to collate HOT records!"}), 500

        return jsonify(results), 200
    
    def get_unverified_records(self, page):
        pass