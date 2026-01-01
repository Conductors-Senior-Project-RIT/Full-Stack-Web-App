import database.src.db.record_types as record_types
from database.src.db.database_status import *
from database.src.service.service_core import *

# Temporary constant for number of results per page
RESULTS_NUM = 250

class TrainHistoryService(BaseService):
    def __init__(self, record_type: int):
        try:
            self.repo = record_types.get_record_repository(record_type)
            super().__init__("Train History")
        except RepositoryRecordInvalid(record_type) as e:
            raise ServiceInvalidArgument(self, str(e))


    def get_train_history(self, record_id: int, page_num: int):
        try:
            return self.repo.get_train_history(record_id, page_num, RESULTS_NUM)
        except RepositoryTimeoutError:
            raise ServiceTimeoutError(self)
        except (RepositoryInternalError, RepositoryParsingError) as e:
            raise ServiceInternalError(self, str(e))
        
        
    def post_train_history(self, args: dict, datetime_str: str):
        try:
            # Don't need to check num results, creation errors are checked in repo
            _, recovery_request = self.repo.create_train_record(args, datetime_str)
            self.add_new_pin(args["unit_addr"])
            
            has_notification = self.check_recent_notification(args["unit_addr"], args["station_id"])
            
            if not has_notification and not recovery_request:
                # Send notification for HOT
                pass
        
        except RepositoryTimeoutError:
            raise ServiceTimeoutError(self)
        except (RepositoryInternalError, RepositoryParsingError) as e:
            raise ServiceInternalError(self, str(e))
        except RepositoryNotFoundError as e:
            raise ServiceResourceNotFound(self, str(e))
        except KeyError as e:
            raise ServiceInvalidArgument(self, e.args[0])
        
        
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