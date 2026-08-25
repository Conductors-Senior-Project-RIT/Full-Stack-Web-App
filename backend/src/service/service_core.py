from ..db.db_core.exceptions import RError
from ..global_core.exceptions import (
    LayerError,
    LayerErrorHandler,
    LayerErrorInvoker,
    LayerErrorWrapper,
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
    """
    A class used to provide exception translation for the Service layer.
    
    All exceptions raised in the Service layer (excluding [`ServiceError`][s-error-types]
    subclasses) are caught and translated into a [`ServiceError`][s-error-types] 
    using this class. Any exceptions will be translated to a [`ServiceInternalError`][s-error-types] 
    if they are not explicitly mapped in the [`SERVICE_ERROR_MAP`][s-error-mapping]. 

    Attributes:
        error_map (dict): A mapping of exception types to their corresponding
            [`ServiceError`][s-error-types] subclass and a boolean indicating whether the error should
            be publicly shown. Defaults to [`SERVICE_ERROR_MAP`][s-error-mapping].
        base_exception (Type[ServiceError]): The fallback exception class for the
            Repository layer. Defaults to [`ServiceInternalError`][s-error-types].
        exclude (Type[ServiceError]): The exception class to exclude from
            translation. Defaults to [`ServiceError`][r-error-types].
    """
    
    error_map = SERVICE_ERROR_MAP
    base_exception = ServiceInternalError
    exclude = ServiceError

class ServiceErrorWrapper(LayerErrorWrapper):
    """A mixin that wraps class methods with Service layer exception handling during 
    subclass initialization. Further information on the implementation and methods can be found in
    [LayerErrorWrapper][src.global_core.exceptions.LayerErrorWrapper]."""
    error_handler = ServiceErrorHandler
    
class ServiceErrorInvoker(LayerErrorInvoker):
    """A mixin that encapsulates methods for validating arguments, raising, and/or translating 
    exceptions within the Service layer. Further information on the implementation and methods can be found in
    [LayerErrorInvoker][src.global_core.exceptions.LayerErrorInvoker]."""
    error_handler = ServiceErrorHandler
    
