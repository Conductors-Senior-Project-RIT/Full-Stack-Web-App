from .base_record_repo import RecordRepository
from .db_core.repository import repository_error_handler
from .db_core.models import Base

class DPURepository(RecordRepository):
    def __init__(self, session):
        raise NotImplementedError
    
    @repository_error_handler()
    def get_train_history(self, id, page, num_results):
        raise NotImplementedError

    @repository_error_handler()
    def create_train_record(self, args, datetime_string):
        raise NotImplementedError

    @repository_error_handler()
    def get_recent_station_records(self, station_id):
        raise NotImplementedError

    def get_record_collation(self, page: int, num_results: int, verified: bool | None = None):
        raise NotImplementedError