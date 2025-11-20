from abc import ABC, abstractmethod

from flask import Response

class Record_API_Strategy(ABC):
    @abstractmethod
    def get_train_history(self, id: int, page: int, results_num: int) -> Response:
        pass