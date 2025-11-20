from flask import Response
from api_strat import Record_API_Strategy

class DPU_API_Strategy(Record_API_Strategy):
    def get_train_history(self, id, page, results_num) -> Response:
        return super().get_train_history(page, results_num)