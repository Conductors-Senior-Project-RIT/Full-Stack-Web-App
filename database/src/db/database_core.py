from functools import wraps
from record_types import RecordTypes
from core.exceptions import LayerError, layer_error_handler, translate_error
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.exc import *

class BaseRepository:
    def __init__(self, session: scoped_session):
        if self.session is None:
            raise RepositorySessionError()
        self.session = session
        
        
    # def __init_subclass__(cls, **kwargs):
    #     super().__init_subclass__(**kwargs)
    #     for attr, value in cls.__dict__.items():
    #         # If the value is a function, then wrap
    #         if callable(value):
    #             # Register class funtion from name (attr), with the error handler decorator wrapping function (value)
    #             wrapped = layer_error_handler(value, REPOSITORY_ERROR_MAP, RepositoryInternalError)
    #             setattr(cls, attr, wrapped)
        

class RepositoryError(LayerError):
    default_message = "Unknown repository error occurred!"
        
class RepositorySessionError(RepositoryError):
    default_message = "Session was not initialized to database!"
        
class RepositoryConnectionError(RepositoryError):
    default_message = "Error connecting to the database!"

class RepositoryInternalError(RepositoryError):
    default_message = "An internal error occurred!"
        
class RepositoryParsingError(RepositoryError):
    default_message = "An error occurred while parsing results!"
        
class RepositoryNotFoundError(RepositoryError):
    default_message = "Could not find value in database!" 
        
class RepositoryRecordInvalid(RepositoryError):
    valid_types = list(RecordTypes._value2member_map_)
    default_message = f"Invalid record type provided! Value must be between {valid_types[0]} and {valid_types[-1]}." 
        
REPOSITORY_ERROR_MAP = {
    (TimeoutError, UnboundExecutionError, InterfaceError, NoSuchModuleError): 
        (RepositoryConnectionError, False),
    (SQLAlchemyError): (RepositoryInternalError, False),
    (TypeError, KeyError, IndexError, ZeroDivisionError): (RepositoryParsingError, False)
}        


def repository_error_handler(message: str | None = None):
    def decorator(func):
        return layer_error_handler(
            func, 
            error_map=REPOSITORY_ERROR_MAP, 
            base_exception=RepositoryInternalError,
            exclude=RepositoryError,
            message=message
        )
    
    return decorator


def repository_error_translator(
    e: Exception,
    caller_name: str | None = None,
    point_of_error: str | None = None,
    message: str | None = None
):
    return translate_error(
        e,
        REPOSITORY_ERROR_MAP,
        RepositoryInternalError,
        caller_name,
        point_of_error,
        message
    )
    