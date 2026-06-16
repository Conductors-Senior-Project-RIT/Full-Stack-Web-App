from ..db.db_core.exceptions import (
    RepositoryConnectionError,
    RepositoryExistingRowError,
    RepositoryInternalError,
    RepositoryInvalidArgumentError,
    RepositoryNotFoundError,
    RepositoryParsingError,
    RepositorySessionError,
    LayerError,
)
from ..global_core.exceptions import LayerErrorWrapper
from ..db.record_types import RepositoryRecordInvalid


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


# Maps a Repository layer error to a corresponding Service layer error, and whether the lower layer message should be shown
SERVICE_ERROR_MAP = {
    RepositorySessionError: (ServiceInternalError, True),
    RepositoryExistingRowError: (ServiceExistingResourceError, True),
    RepositoryParsingError: (ServiceParsingError, False),
    RepositoryConnectionError: (ServiceTimeoutError, False),
    RepositoryNotFoundError: (ServiceResourceNotFound, True),
    RepositoryRecordInvalid: (ServiceInvalidArgument, True),
    RepositoryInvalidArgumentError: (ServiceInvalidArgument, True),
    RepositoryInternalError: (ServiceInternalError, False),
}

class ServiceErrorWrapper(LayerErrorWrapper):
    error_map = SERVICE_ERROR_MAP
    base_exception = ServiceInternalError
    exclude = ServiceError
