from backend.src.db.base_record_repo import RecordRepository
from backend.src.db.database_core import repository_error_handler


class DPURepository(RecordRepository):
    def __init__(self, session):
        super().__init__(
            session, 
            "DPURecords", 
            "DPU Record", 
            "dpu"
        )
    
    @repository_error_handler()
    def get_train_history(self, id, page, num_results):
        raise NotImplementedError

    @repository_error_handler()
    def create_train_record(self, args, datetime_string):
        raise NotImplementedError

    @repository_error_handler()
    def get_recent_station_records(self, station_id):
        raise NotImplementedError

    @repository_error_handler()
    def parse_station_records(self, station_records):
        raise NotImplementedError

    def get_record_collation(self, page):
        raise NotImplementedError

    def get_records_by_verification(self, page, verified):
        raise NotImplementedError

