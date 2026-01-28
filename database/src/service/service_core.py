from abc import ABC
from enum import Enum

from database.src.db.record_types import RecordTypes
    
    
class BaseService(ABC):
    def __init__(self, name: str):
        self._name = f"{name} Service"
        
    def get_name(self) -> str:
        return self._name


class ServiceError(Exception):
    def __init__(self, service: BaseService, message: str):
        self._caller = service.get_name()
        super().__init__(message)


class ServiceInternalError(Exception):
    def __init__(self, service: BaseService, *args):
        super().__init__(service, f"Encountered an internal error: {args}")
        
        
class ServiceTimeoutError(Exception):
    def __init__(self, service: BaseService):
        super().__init__(service, "Timed out!")
        

class ServiceParsingError(Exception):
    def __init__(self, service: BaseService):
        super().__init__(service, "Could not parse results!")
        
        
class ServiceResourceNotFound(Exception):
    def __init__(self, service, *args):
        super().__init__(service, str(args))


class ServiceInvalidArgument(Exception):
    def __init__(self, service: BaseService, *args):
        super().__init__(service, f"Invalid argument provided: {args}")

    