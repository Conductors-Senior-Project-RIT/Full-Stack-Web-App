from typing import Type

from sqlalchemy.exc import DataError, SQLAlchemyError, UnboundExecutionError,InterfaceError, NoSuchModuleError

from ...global_core.exceptions import LayerError, layer_error_handler, translate_error

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
    default_message = "Could not find value in database!" 
    
class RepositoryInvalidArgumentError(RepositoryError):
    default_message = "Invalid argument provided!" 
    
class RepositoryExistingRowError(RepositoryError):
    default_message = "The provided row already exists!"

# class RepositoryRecordInvalid(RepositoryError):
#     valid_types = list(RecordTypes._value2member_map_)
#     default_message = f"Invalid record type provided! Value must be between {valid_types[0]} and {valid_types[-1]}."

REPOSITORY_ERROR_MAP = {
    (TimeoutError, UnboundExecutionError, InterfaceError, NoSuchModuleError): 
        (RepositoryConnectionError, False),
    (TypeError, KeyError, ValueError, IndexError, ZeroDivisionError, DataError): 
        (RepositoryParsingError, False),
    SQLAlchemyError: (RepositoryInternalError, False)
    
}

def repository_error_translator(
    e: Exception,
    caller_name: str | None = None,
    point_of_error: str | None = None,
    message: str | None = None,
    exclude: tuple[Type[Exception]] | Type[Exception] | None = None
):
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
    return layer_error_handler(
        error_map=REPOSITORY_ERROR_MAP, 
        base_exception=RepositoryInternalError,
        exclude=RepositoryError if not exclude else exclude,
        message=message
    )