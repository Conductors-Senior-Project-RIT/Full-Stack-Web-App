from flask import Response
from api_strat import Record_API_Strategy
from typing import Any

class DPU_Service_Strategy(Record_API_Strategy):
    def get_train_history(self, id, page, results_num) -> Response:
        return super().get_train_history(page, results_num)
    
    def post_train_record(self, args, datetime_str):
        return super().post_train_history(args, datetime_str)

    def parse_station_records(self, station_records: list[tuple[Any, ...]]) -> list[dict[str, Any]] | None:
        return None