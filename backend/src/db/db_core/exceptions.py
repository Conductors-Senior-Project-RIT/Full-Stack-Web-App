from typing import Optional, Type

from sqlalchemy.exc import DataError, IntegrityError, MultipleResultsFound, NoResultFound, ProgrammingError, SQLAlchemyError, UnboundExecutionError,InterfaceError, NoSuchModuleError

from ...global_core.exceptions import LayerError, layer_error_handler, translate_error, wrap_error_handler

#################################################
##  REPOSITORY EXCEPTION HANDLING DEFINITIONS  ##
#################################################

class RepositoryError(LayerError):
    default_message = "Unknown repository error occurred!"
        
class RepositorySessionError(RepositoryError):
    default_message = "Session was not initialized to database!"
        
class RepositoryConnectionError(RepositoryError):
    default_message = "Error connecting to the database!"

class RepositoryInternalError(RepositoryError):
    default_message = "An internal error occurred!"
        
class RepositoryParsingError(RepositoryError):
    default_message = "An error occurred while parsing values!"
        
class RepositoryNotFoundError(RepositoryError):
    default_message = "Could not find resource!" 
    
class RepositoryInvalidArgumentError(RepositoryError):
    default_message = "Invalid argument provided!" 
    
class RepositoryExistingRowError(RepositoryError):
    default_message = "The provided row already exists!"


# It should be the Service layer's job to determine what error messages are shown to the API
REPOSITORY_ERROR_MAP = {
    (TimeoutError, UnboundExecutionError, InterfaceError, NoSuchModuleError): 
        (RepositoryConnectionError, True),
    (TypeError, KeyError, ValueError, IndexError, ZeroDivisionError, 
     DataError, ProgrammingError, IntegrityError): (RepositoryParsingError, True),
    NoResultFound: (RepositoryNotFoundError, True),
    MultipleResultsFound: (RepositoryExistingRowError, True),
    SQLAlchemyError: (RepositoryInternalError, True)
}


def wrap_repository_error_handler(func):
    """Wraps a function with a layer error handler that translates exceptions into a
    `RepositoryError`.

    Args:
        func (callable): The function to wrap.

    Returns:
        callable: The wrapped function with repository error handling.
    """
    return wrap_error_handler(
        func=func,
        error_map=REPOSITORY_ERROR_MAP, 
        base_exception=RepositoryInternalError,
        exclude=RepositoryError
    )


def repository_error_translator(
    e: Exception,
    caller_name: Optional[str] = None,
    point_of_error: Optional[str] = None,
    message: Optional[str] = None,
    exclude: Optional[tuple[Type[Exception]] | Type[Exception]] = None
) -> RepositoryError:
    """Translates a provided exception into a `RepositoryError`. See `layer_error_handler`
    for more details.

    Args:
        e (Exception): An exception that is to be translated.
        caller_name (str, optional): The class that called this function. Defaults to
            None.
        point_of_error (str, optional): The location/function the error occurred in.
            Defaults to None.
        message (str, optional): An optional message to provide in a `RepositoryError`.
            Defaults to None.
        exclude (tuple[Type[Exception]] | Type[Exception], optional): A single or
            collection of exceptions to exclude from translation. Defaults to None.

    Returns:
        RepositoryError: If a matching translation is found in `error_map`, a subclass
            instance of `RepositoryError` is returned. In the case a match is not found,
            a `RepositoryInternalError` is instantiated and returned as a fallback,
            preventing lower-level implementation details from propagating upwards. If
            the provided exception `e` is an instance with a matching type in `exclude`,
            it is returned as-is.
    """
    return translate_error(
        e,
        REPOSITORY_ERROR_MAP,
        RepositoryInternalError,
        caller_name,
        point_of_error,
        message,
        RepositoryError if not exclude else exclude
    )
    
def repository_error_handler(
    message: Optional[str] = None, 
    exclude: Optional[tuple[Type[Exception]] | Type[Exception]] = None
):
    """Decorator used to provide error translation for exceptions thrown in the Repository
    layer. See `layer_error_handler` for more implementation and argument details.

    Examples:
        ```
        @repository_error_translator()
            def some_repository_method(self):
                ...
        ```


    Args:
        message (str, optional): An optional message to provide in a `RepositoryError`.
            Defaults to None.
        exclude (tuple[Type[Exception]] | Type[Exception], optional): A single or
            collection of exceptions to exclude from translation. Defaults to None.

    Returns:
        callabe: The original function wrapped with exception handling logic, with its
            signature and metadata preserved.
    """
    return layer_error_handler(
        error_map=REPOSITORY_ERROR_MAP, 
        base_exception=RepositoryInternalError,
        exclude=RepositoryError if not exclude else exclude,
        message=message
    )