import datetime
import db.record_types as record_types
import db.station_repo as station_repo
from db.database_status import *
from service.service_core import *

# Temporary constant for number of results per page
RESULTS_NUM = 250

class RecordService(BaseService):
    def __init__(self, record_type: int):
        try:
            self.repo = record_types.get_record_repository(record_type) if record_type is not None else None
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
        return results is not None and len(results) > 0
        
    def add_new_pin(self, unit_addr: str):
        self.attempt_auto_fill(unit_addr)
        
        resp_id = self.repo.get_unit_record_ids(unit_addr, True)
        result = self.repo.add_new_pin(resp_id, unit_addr)
        
    def attempt_auto_fill(self, unit_addr: str):
        symb = self.repo.check_for_record_field(unit_addr, "symbol_id")
        engi = self.repo.check_for_record_field(unit_addr, "engine_num")
        record_id = self.repo.get_unit_record_ids(unit_addr, True)
        
        symb = symb if symb is not None else -1
        engi = engi if engi is not None else -1
        
        # Use the signal update function used in signal updater because the perform the same task
        self.signal_update(record_id, symb, engi)
            
    # Signal Updater
    def signal_update(self, record_id: int, symbol_id: int, engine_id: int):
        try:
            if symbol_id != -1:
                self.repo.update_record_field(record_id, symbol_id, "symbol_id")
            
            if engine_id != -1:
                self.repo.update_record_field(record_id, engine_id, "engine_num")
        
        except RepositoryTimeoutError:
            raise ServiceTimeoutError(self)
        except RepositoryInternalError as e:
            raise ServiceInternalError(str(e))


    # Data Collation
    def collate_records(self, page: int) -> list[dict[str, str]]:
        try:
            return self.repo.get_record_collation(page)
        except RepositoryTimeoutError:
            raise ServiceTimeoutError(self)
        except (RepositoryInternalError, RepositoryParsingError) as e:
            raise ServiceInternalError(self, str(e))
    
    
    # Log Verification
    def get_unverified_records(self, page: int) -> list[dict[str, str]]:
        try:
            return self.repo.get_records_by_verification(page, False)
        except RepositoryTimeoutError:
            raise ServiceTimeoutError(self)
        except (RepositoryInternalError, RepositoryParsingError) as e:
            raise ServiceInternalError(self, str(e))
        
    def verify_record(self, record_id: int, symbol_id: int, engine_id: int):
        try:
            self.repo.verify_record(record_id, symbol_id, engine_id)
        except RepositoryTimeoutError:
            raise ServiceTimeoutError(self)
        except RepositoryNotFoundError as e:
            raise ServiceResourceNotFound(self, str(e))
        except RepositoryInternalError as e:
            raise ServiceInternalError(self, str(e))
        
        
    # Time frame pull
    def time_frame_pull(self, record_type: int, time_range: str, recent: bool, station_id: int, station_name: str):
        try:
            time_increments = time_range.split(":")
            
            curr_date = datetime.datetime.now()
            delta = datetime.timedelta(
                hours=int(time_increments[0]),
                minutes=int(time_increments[1]),
                seconds=int(time_increments[2]),
            )
            altered_time = curr_date - delta
            dt_str = altered_time.strftime("%Y-%m-%d %H:%M:%S")
            
            
            if station_id == -1:
                if station_name:
                    station_id = station_repo.get_station_id(station_name)
            
            if record_type == -1:
                chosen_repos = (
                    record_types.get_all_repositories()
                    if record_type == -1 else
                    [record_types.get_record_repository(record_type)]
                )

            results = []
            for repo in chosen_repos:
                repo_resp = repo.get_records_in_timeframe(station_id, dt_str, recent)
                results.append(repo_resp)
            
            results.sort(key=lambda x: x["date_rec"], reverse=True)
            return results
        
        except (IndexError, KeyError) as e:
            raise ServiceParsingError(self, str(e))
        except RepositoryRecordInvalid as e:
            raise ServiceInvalidArgument(self, str(e))
        except RepositoryTimeoutError:
            raise ServiceTimeoutError(self)
        except (RepositoryInternalError, RepositoryParsingError) as e:
            raise ServiceInternalError(self, str(e))
        