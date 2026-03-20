from collections.abc import Iterable
from typing import Any, Protocol, Type, runtime_checkable

from sqlalchemy import Row, Sequence
from sqlalchemy.exc import SQLAlchemyError, UnboundExecutionError,InterfaceError, NoSuchModuleError
from sqlalchemy.orm.scoping import scoped_session

from ..core.exceptions import LayerError, layer_error_handler, translate_error

@runtime_checkable
class AsDictConvertible(Protocol):
    def _asdict(self) -> dict[str, Any]: ...
    @property
    def _mapping(self) -> dict[str, Any]: ...
    

class BaseRepository:
    def __init__(self, session: scoped_session):
        if session is None:
            raise RepositorySessionError()
        self.session = session
    
    @classmethod
    def rows_to_dicts(cls, rows: Sequence[AsDictConvertible]) -> list[dict[str, Any]]:
        results = []
        for r in rows:
            if isinstance(r, (Row, Iterable)) and len(r) == 1:
                row = r[0]
            else:
                row = r
            
            if hasattr(row, "_mapping"):
                results.append(dict(row._mapping))
            elif hasattr(row, "_asdict"):
                results.append(row._asdict())
            else:
                raise RepositoryParsingError(
                    cls.__name__,
                    "row_to_dicts",
                    "A provided does not contain functionality to map attributes to values!",
                    show_error=False
                )
                
        return results
        
        
    # def __init_subclass__(cls, **kwargs):
    #     super().__init_subclass__(**kwargs)
    #     for attr, value in cls.__dict__.items():
    #         # If the value is a function, then wrap
    #         if callable(value):
    #             # Register class function from name (attr), with the error handler decorator wrapping function (value)
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
    default_message = "An error occurred while parsing values!"
        
class RepositoryNotFoundError(RepositoryError):
    default_message = "Could not find value in database!" 
    
class RepositoryInvalidArgumentError(RepositoryError):
    default_message = "Invalid argument provided!" 

# class RepositoryRecordInvalid(RepositoryError):
#     valid_types = list(RecordTypes._value2member_map_)
#     default_message = f"Invalid record type provided! Value must be between {valid_types[0]} and {valid_types[-1]}."

REPOSITORY_ERROR_MAP = {
    (TimeoutError, UnboundExecutionError, InterfaceError, NoSuchModuleError): 
        (RepositoryConnectionError, False),
    SQLAlchemyError: (RepositoryInternalError, False),
    (TypeError, KeyError, IndexError, ZeroDivisionError): (RepositoryParsingError, False)
}

def repository_error_handler(
    message: str | None = None, 
    exclude: tuple[Type[Exception]] | Type[Exception] | None = None
):
    def decorator(func):
        return layer_error_handler(
            func, 
            error_map=REPOSITORY_ERROR_MAP, 
            base_exception=RepositoryInternalError,
            exclude=RepositoryError if not exclude else exclude,
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