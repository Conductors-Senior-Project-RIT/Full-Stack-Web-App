from db.database_core import *
from util.error_handling import BaseLayerError, database_error_handler
from functools import wraps


TESTING_ENABLED = True


class BaseService:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for attr, value in cls.__dict__.items():
            # If the value is a function, then wrap
            if callable(value):
                # Register class funtion from name (attr), with the error handler decorator wrapping function (value)
                wrapped = repository_error_handler(value)
                setattr(cls, attr, wrapped)


class ServiceError(Exception):
    default_message = "Unkown error occurred!"
    
    def __init__(self, caller_name: str, message = None, show_error = False):
        public = self.default_message
        if show_error and message:
            public = f"{public[0:-1]}: {message}"
        super().__init__(f"[{caller_name}] {public}")


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
    RepositoryTimeoutError: (ServiceTimeoutError, False),
    RepositoryNotFoundError: (ServiceResourceNotFound, False),
    RepositoryRecordInvalid: (ServiceInvalidArgument, True)
}
    
    
def repository_error_handler(func):
    """This function acts as a decorator to provide Service layer error translation for
    Repository layer errors that are raised.

    Args:
        func (`function`): The function to wrap with error handling in the Service layer.

    Raises:
        `ServiceError`: Raises a corresponding ServiceError depending on the RepositoryError
        raised. A ServiceInternalError is raised in the case of an unspecified base Exception.

    Returns:
        `function`: Returns a function wrapped with RepositoryError handling.
    """
    @wraps(func)
    def decorator(*args, **kwargs):
        # Reference the Service instance calling the function
        service_instance = args[0]
        try:
            # Return our wrapped function
            return func(*args, **kwargs)
        except Exception as e:
            # Find the first RepositoryError that matches the raised exception
            error_class = next((SERVICE_ERROR_MAP[cls] for cls in SERVICE_ERROR_MAP if isinstance(e, cls)), None)
    
            # If a match was found, raise the specific error
            if error_class:
                service_exception, show_error = error_class
                # "from e" is important as it allows us to trace the error to the Repository layer
                if TESTING_ENABLED or show_error:
                    raise service_exception(service_instance, str(e)) from e
                raise service_exception(service_instance)
            
            # Otherwise, raise a generic internal error
            raise ServiceInternalError(service_instance) from e
    
    return decorator
