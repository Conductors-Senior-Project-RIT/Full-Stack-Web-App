from typing import Type

from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError, SQLAlchemyError, UnboundExecutionError,InterfaceError, NoSuchModuleError

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


REPOSITORY_ERROR_MAP = {
    (TimeoutError, UnboundExecutionError, InterfaceError, NoSuchModuleError): 
        (RepositoryConnectionError, False),
    (TypeError, KeyError, ValueError, IndexError, ZeroDivisionError, 
     DataError, ProgrammingError, IntegrityError): 
        (RepositoryParsingError, False),
    SQLAlchemyError: (RepositoryInternalError, False)
    
}


def wrap_repository_error_handler(func):
    """Wraps a function with a layer error handler that translates exceptions into a
    `RepositoryError`.

    Args:
        func (callable): The function to wrap.
        error_map (dict): A mapping of lower layer exceptions to RepositoryErrors and
            whether to show the original message.
        base_exception (Type[RepositoryError]): The base RepositoryError to use if an
            exception is not found in the error_map.
        exclude (Type[RepositoryError] or tuple of Type[RepositoryError]): A
            RepositoryError or tuple of RepositoryErrors to exclude from being caught
            and translated by the error handler.

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
    caller_name: str | None = None,
    point_of_error: str | None = None,
    message: str | None = None,
    exclude: tuple[Type[Exception]] | Type[Exception] | None = None
) -> RepositoryError:
    """Translates a provided exception into a `RepositoryError`. See
    :func:`layer_error_handler` for more details.

    Args:
        e (Exception): _description_
        caller_name (str | None, optional): _description_. Defaults to None.
        point_of_error (str | None, optional): _description_. Defaults to None.
        message (str | None, optional): _description_. Defaults to None.
        exclude (tuple[Type[Exception]] | Type[Exception] | None, optional):
            _description_. Defaults to None.

    Returns:
        RepositoryError: If a matching translation is found in `error_map`, a subclass
            instance of :class:`RepositoryError` is returned. In the case a match is not
            found, a :class:`RepositoryInternalError` is instantiated and returned as a
            fallback, preventing lower-level implementation details from propagating
            upwards. If the provided exception `e` is an instance with a matching type
            in `exclude`, it is returned as-is.
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
    message: str | None = None, 
    exclude: tuple[Type[Exception]] | Type[Exception] | None = None
):
    """Decorator used to provide error translation for exceptions thrown in the Repository
    layer. See :func:`layer_error_handler` for more implementation and argument details.

    Examples:
        ```
        @repository_error_translator()
            def some_repository_method(self):
                ...
        ```


    Args:
        e (Exception):
        caller_name (str | None, optional): Defaults to None.
        point_of_error (str | None, optional): Defaults to None.
        message (str | None, optional): Defaults to None.
        exclude (tuple[Type[Exception]] | Type[Exception] | None, optional): Defaults to
            None.

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