from sqlalchemy.exc import (
    DataError, 
    IntegrityError, 
    MultipleResultsFound, 
    NoResultFound, 
    ProgrammingError,
    SQLAlchemyError,
    UnboundExecutionError,
    InterfaceError,
    NoSuchModuleError
)
from psycopg2.errors import UniqueViolation

from ...global_core.exceptions import LayerError, LayerErrorHandler, LayerErrorWrapper, LayerErrorInvoker

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
    """Raised when a invalid record type is provided to `get_record_repository`."""

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
    error_map = REPOSITORY_ERROR_MAP
    base_exception = RepositoryInternalError
    exclude = RepositoryError
    error_origin_name = "orig"
    
class RepositoryErrorWrapper(LayerErrorWrapper):
    error_handler = RepositoryErrorHandler
    
class RepositoryErrorInvoker(LayerErrorInvoker):
    error_handler = RepositoryErrorHandler
