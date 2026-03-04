from ..db.database_core import RepositorySessionError, RepositoryParsingError, RepositoryNotFoundError, \
    RepositoryInternalError, RepositoryConnectionError
from ..core.exceptions import LayerError, layer_error_handler
from ..db.record_types import RepositoryRecordInvalid # exists separately because of circular dependency issue; eventually needs to be refactored slightly
# from ..api.error_handler import BaseLayerError, database_error_handler



TESTING_ENABLED = True


class BaseService:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for attr, value in cls.__dict__.items():
            # If the value is a function, then wrap
            if callable(value):
                # Register class funtion from name (attr), with the error handler decorator wrapping function (value)
                wrapped = layer_error_handler(value, SERVICE_ERROR_MAP, ServiceInternalError)
                setattr(cls, attr, wrapped)


class ServiceError(LayerError):
    default_message = "Unknown service error occurred!"


class ServiceInternalError(ServiceError):
    default_message = "Internal error occurred!"
        
        
class ServiceTimeoutError(ServiceError):
    default_message = "Timed out!"
        

class ServiceParsingError(ServiceError):
    default_message = "Could not parse results!"
        
        
class ServiceResourceNotFound(ServiceError):
    default_message = "Resource not found!"


class ServiceInvalidArgument(ServiceError):
    default_message = "Invalid argument provided!"


# Maps a Repository layer error to a corresponding Service layer error, and whether the lower layer message should be shown
SERVICE_ERROR_MAP = {
    RepositorySessionError: (ServiceInternalError, True),
    RepositoryInternalError: (ServiceInternalError, False),
    RepositoryParsingError: (ServiceInternalError, False),
    RepositoryConnectionError: (ServiceTimeoutError, False),
    RepositoryNotFoundError: (ServiceResourceNotFound, True),
    RepositoryRecordInvalid: (ServiceInvalidArgument, True)
}
    
