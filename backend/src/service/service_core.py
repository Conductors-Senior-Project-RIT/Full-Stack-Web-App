from ..db.db_core.exceptions import (
    RepositoryConnectionError,
    RepositoryExistingRowError,
    RepositoryInternalError,
    RepositoryInvalidArgumentError,
    RepositoryNotFoundError,
    RepositoryParsingError,
    RepositorySessionError,
    wrap_error_handler,
    LayerError,
)
from ..db.record_types import RepositoryRecordInvalid



class BaseService:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for attr, value in cls.__dict__.items():
            # If the value is a function, then wrap
            if callable(value) and not getattr(value, "_is_wrapped", False):                
                # Register class funtion from name (attr), with the error handler decorator wrapping function (value)
                wrapped = wrap_error_handler(
                    func=value,
                    error_map=SERIVCE_ERROR_MAP,
                    base_exception=ServiceInternalError,
                )
                wrapped._is_wrapped = True
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


class ServiceExistingResourceError(ServiceError):
    default_message = "Resource already exists!"


class ServiceInvalidArgument(ServiceError):
    default_message = "Invalid argument provided!"


# Maps a Repository layer error to a corresponding Service layer error, and whether the lower layer message should be shown
SERIVCE_ERROR_MAP = {
    RepositorySessionError: (ServiceInternalError, True),
    RepositoryExistingRowError: (ServiceExistingResourceError, True),
    RepositoryParsingError: (ServiceParsingError, False),
    RepositoryConnectionError: (ServiceTimeoutError, False),
    RepositoryNotFoundError: (ServiceResourceNotFound, True),
    RepositoryRecordInvalid: (ServiceInvalidArgument, True),
    RepositoryInvalidArgumentError: (ServiceInvalidArgument, True),
    RepositoryInternalError: (ServiceInternalError, False),
}
