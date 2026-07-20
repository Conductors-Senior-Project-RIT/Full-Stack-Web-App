from ..db.db_core.exceptions import RError
from ..global_core.exceptions import (
    LayerErrorHandler, 
    LayerErrorInvoker, 
    LayerErrorWrapper, 
    LayerError
)


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

class ServiceExistingResourceError(ServiceError):
    default_message = "Resource already exists!"

class ServiceInvalidArgument(ServiceError):
    default_message = "Invalid argument provided!"
        
class ServiceEmailError(ServiceError):
    default_message = "Error sending email!"
    
    
class SError:
    INTERNAL = ServiceInternalError
    TIMEOUT = ServiceTimeoutError
    PARSING = ServiceParsingError
    NOT_FOUND = ServiceResourceNotFound
    EXISTING = ServiceExistingResourceError
    INVALID_ARG = ServiceInvalidArgument
    EMAIL = ServiceEmailError


# Maps a Repository layer error to a corresponding Service layer error, and whether the lower layer message should be shown
SERVICE_ERROR_MAP = {
    RError.EXISTING: (SError.EXISTING, True),
    RError.PARSING: (SError.PARSING, False),
    RError.CONNECTION: (SError.TIMEOUT, False),
    RError.NOT_FOUND: (SError.NOT_FOUND, True),
    RError.INVALID_RECORD: (SError.INVALID_ARG, True),
    RError.INVALID_ARG: (SError.INVALID_ARG, True),
    RError.INTERNAL: (SError.INTERNAL, False),
}


class ServiceErrorHandler(LayerErrorHandler):
    error_map = SERVICE_ERROR_MAP
    base_exception = ServiceInternalError
    exclude = ServiceError

class ServiceErrorWrapper(LayerErrorWrapper):
    error_handler = ServiceErrorHandler
    
class ServiceErrorInvoker(LayerErrorInvoker):
    error_handler = ServiceErrorHandler
    
