from database.src.db.base_record_repo import NotFoundError
from database.src.db.hot_repo import RepositoryError
from database.src.service.service_status import InvalidRecordError, ServiceError, ServiceStatusCode
from database.src.db import record_types

# Temporary constant for number of results per page
RESULTS_NUM = 250

class TrainHistoryService:
    def __init__(self, record_type: int):
        try:
            self.repo = record_types.get_record_repository(record_type)
        except InvalidRecordError as e:
            raise ValueError(str(e))


    def get_train_history(self, record_id: int, page_num: int):
        try:
            return self.repo.get_train_history(record_id, page_num, RESULTS_NUM)
        except RepositoryError as e:
            raise ServiceError(str(e))
        
        
    def post_train_history(self, args: dict, datetime_str: str):
        try:
            # Don't need to check num results, creation errors are checked in repo
            _, recovery_request = self.repo.create_train_record(args, datetime_str)
            self.add_new_pin(args["unit_addr"])
            
            has_notification = self.check_recent_notification(args["unit_addr"], args["station_id"])
            
            if not has_notification and not recovery_request:
                # Send notification for HOT
                pass
            
        except RepositoryError as e:
            raise ServiceError(str(e))
        except NotFoundError as e:
            raise ValueError(str(e))
        
        
    def check_recent_notification(self, unit_addr: str, station_id: int) -> bool:
        results = self.repo.get_recent_trains(unit_addr, station_id)
        return results is not None or len(results) > 0
        
    def add_new_pin(self, unit_addr: str):
        self.attempt_auto_fill(unit_addr)
        
        resp_id = self.repo.get_unit_record_ids(unit_addr, True)
        result = self.repo.add_new_pin(resp_id, unit_addr)
        
    def attempt_auto_fill(self, unit_addr: str):
        symb = self.repo.check_for_record_field(unit_addr, "symbol_id")
        engi = self.repo.check_for_record_field(unit_addr, "engine_num")
        record_id = self.repo.get_unit_record_ids(unit_addr, True)
        
        if symb:
            resp = self.repo.update_record_field(record_id, symb, "symbol_id")
            
        if engi:
            resp = self.repo.update_record_field(unit_addr, engi, "engine_num")
        else:
            print("No engine number to update!")