from abc import ABC, abstractmethod
from argparse import Namespace

from flask import Response

class Record_API_Strategy(ABC):
    @abstractmethod
    def get_train_history(self, id: int, page: int, results_num: int) -> Response:
        pass
    
    @abstractmethod
    def post_train_history(self, args: Namespace, datetime_str: str):
        pass
    
    @abstractmethod
    def add_new_pin(self, unit_addr: str):
        pass
    
    @abstractmethod
    def attempt_auto_fill(self, unit_addr: str):
        pass