import datetime
from typing import Any

import backend.src.db.record_types as record_types
from ..db.base_record_repo import RecordRepository
from ..db.station_repo import StationRepository
from ..service.service_core import *

# Constant for number of results per page during collation
RESULTS_NUM = 250

class RecordService(BaseService):
    def __init__(self, session, record_type: int):
        self._record_repo = (
            [record_types.get_record_repository(session, record_type)] 
            if record_type is not None else 
            record_types.get_all_repositories(session)
        )
        self._station_repo = StationRepository(session)
        self._session = session
        
    
    def get_first_repository(self) -> RecordRepository:
        try:
            return self._record_repo[0]
        except IndexError:
            raise ServiceInternalError("Could not access record repository!")


    def get_train_history(self, record_id: int, page_num: int) -> dict[str, Any]:
        return self.get_first_repository().get_train_history(record_id, page_num, RESULTS_NUM)
        # TODO: Likely can just execute the code snippet below
        # return self.get_first_repository().get(record_id)
        
    def post_train_history(self, args: dict, datetime_str: str):
        # Get a single repository instantiated repository
        repository = self.get_first_repository()
        
        # Don't need to check num results, creation errors are checked in repo
        _, recovery_request = repository.create_train_record(args, datetime_str)
        self.add_new_pin(repository, args["unit_addr"])
        
        has_notification = self.check_recent_notification(repository, args["unit_addr"], args["station_id"])
        
        if not has_notification and not recovery_request:
            # Send notification for HOT
            pass

        
    def check_recent_notification(self, repository: RecordRepository, unit_addr: str, station_id: int) -> bool:
        results = repository.get_recent_trains(unit_addr, station_id)
        return results is not None and len(results) > 0
        
        
    def add_new_pin(self, repository: RecordRepository, unit_addr: str):
        # Update the symbol id and engine num of the new record
        self.attempt_auto_fill(repository, unit_addr)
        # Get most recent record (the one just created)
        resp_id = repository.get_unit_record_ids(unit_addr, True)
        # Make the newly created record the only record where most_recent = True
        repository.add_new_pin(resp_id, unit_addr)
        
        
    def attempt_auto_fill(self, repository: RecordRepository, unit_addr: str):
        """Used to fill a new record with the symbol id and engine num of the previous
        most recent record with the same unit address."""
        # All will return a single int
        symb = repository.get_record_column_by_unit_addr(unit_addr, "symbol_id", True)[-1]
        engi = repository.get_record_column_by_unit_addr(unit_addr, "engine_num", True)[-1]
        record_id = repository.get_unit_record_ids(unit_addr, True)
        
        # Use the signal update function used in signal updater because the perform the same task
        repository.update_signal_values(record_id, symb, engi)
        
    
    # Signal Update
    def signal_update(self, record_id: int, symbol_id: int, engine_num: int):
        result = self.get_first_repository().update_signal_values(record_id, symbol_id, engine_num)
        if result is None:
            raise ServiceResourceNotFound(
                caller_name=self.__class__.__name__,
                message=f"Could not find record with id {record_id} to update signal values, 0 rows updated.",
                show_error=True
            )
        return result["id"]


    # Data Collation
    def collate_records(self, page: int) -> dict[str, list | int]:
        return self.get_first_repository().get_record_collation(page, RESULTS_NUM)
    
    
    # Log Verification
    def get_unverified_records(self, page: int) -> dict[str, list | int]:
        return self.get_first_repository().get_record_collation(page, RESULTS_NUM, False)
        
        
    def verify_record(self, record_id: int, symbol_id: int, engine_id: int):
        self.get_first_repository().verify_record(record_id, symbol_id, engine_id)
        
        
    # Time frame pull
    def time_frame_pull(self, time_range: str, recent: bool, station_id: int, station_name: str):
        try:
            time_increments = time_range.split(":")
            
            curr_date = datetime.datetime.now()
            delta = datetime.timedelta(
                hours=int(time_increments[0]),
                minutes=int(time_increments[1]),
                seconds=int(time_increments[2]),
            )
            timeframe = curr_date - delta
            
            if station_id == -1:
                if station_name:
                    station_id = self._station_repo.get_station_id(station_name)
                
            # Should never occur, but to be safe..
            if len(self._record_repo) < 1:
                raise ServiceInternalError("Could not find valid record access!")

            results = []
            for repo in self._record_repo:
                repo_resp = repo.get_records_in_timeframe(station_id, timeframe, recent)
                results.extend(repo_resp)
            
            results.sort(key=lambda x: x["date_rec"], reverse=True)
            for row in results:
                row["date_rec"] = str(row["date_rec"])
            return results
        
        except (IndexError, KeyError) as e:
            raise ServiceParsingError(self.__class__.__name__, str(e))

        