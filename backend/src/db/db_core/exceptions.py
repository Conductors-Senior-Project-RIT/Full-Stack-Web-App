from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import (
    DataError,
    IntegrityError,
    InterfaceError,
    MultipleResultsFound,
    NoResultFound,
    NoSuchModuleError,
    ProgrammingError,
    SQLAlchemyError,
    UnboundExecutionError,
)

from ...global_core.exceptions import (
    LayerError,
    LayerErrorHandler,
    LayerErrorInvoker,
    LayerErrorWrapper,
)

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
    
class RepositoryRecordInvalid(RepositoryError):
    default_message = "Invalid record type provided! Value must be between 1 and 3."
    

class RError:
    SESSION = RepositorySessionError
    CONNECTION = RepositoryConnectionError
    INTERNAL = RepositoryInternalError
    PARSING = RepositoryParsingError
    NOT_FOUND = RepositoryNotFoundError
    INVALID_ARG = RepositoryInvalidArgumentError
    INVALID_RECORD = RepositoryRecordInvalid
    EXISTING = RepositoryExistingRowError


# It should be the Service layer's job to determine what error messages are shown to the API
REPOSITORY_ERROR_MAP = {
    (TimeoutError, UnboundExecutionError, InterfaceError, NoSuchModuleError): 
        (RError.CONNECTION, True),
    NoResultFound: (RError.NOT_FOUND, True),
    (MultipleResultsFound, UniqueViolation): (RError.EXISTING, True),
    (TypeError, KeyError, ValueError, IndexError, ZeroDivisionError, DataError, ProgrammingError, IntegrityError): 
        (RError.PARSING, True),
    SQLAlchemyError: (RError.INTERNAL, True)
}
    
    
class RepositoryErrorHandler(LayerErrorHandler):
    """
    A class used to provide exception translation for the Repository layer.

    All exceptions raised in the Repository layer (excluding [`RepositoryError`][r-error-types]
    subclasses) are caught and translated into a [`RepositoryError`][r-error-types] 
    using this class. Any exceptions will be translated to a [`RepositoryInternalError`][r-error-types] 
    if they are not explicitly mapped in the [`REPOSITORY_ERROR_MAP`][r-error-mapping]. 
    Exceptions in *SQLAlchemy* also contain a reference to the original *psycopg2* exception 
    in the `orig` attribute, which is used to determine the error type.

    Attributes:
        error_map (dict): A mapping of exception types to their corresponding
            [`RepositoryError`][r-error-types] subclass and a boolean indicating whether the error should
            be publicly shown. Defaults to [`REPOSITORY_ERROR_MAP`][r-error-mapping].
        base_exception (Type[RepositoryError]): The fallback exception class for the
            Repository layer. Defaults to [`RepositoryInternalError`][r-error-types].
        exclude (Type[RepositoryError]): The exception class to exclude from
            translation. Defaults to [`RepositoryError`][r-error-types].
        error_origin_name (str): The attribute name that contains the original exception
            in SQLAlchemy. Defaults to `"orig"`.
    """
    error_map = REPOSITORY_ERROR_MAP
    base_exception = RepositoryInternalError
    exclude = RepositoryError
    error_origin_name = "orig"
    
class RepositoryErrorWrapper(LayerErrorWrapper):
    """A mixin that wraps class methods with Repository layer exception handling during 
    subclass initialization. Further information on the implementation and methods can be found in
    [LayerErrorWrapper][src.global_core.exceptions.LayerErrorWrapper]."""
    error_handler = RepositoryErrorHandler
    
class RepositoryErrorInvoker(LayerErrorInvoker):
    """A mixin that encapsulates methods for validating arguments, raising, and/or translating 
    exceptions within the Repository layer. Further information on the implementation and methods can be found in
    [LayerErrorInvoker][src.global_core.exceptions.LayerErrorInvoker]."""
    error_handler = RepositoryErrorHandler
