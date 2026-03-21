from collections.abc import Iterable
from typing import Any, Generic, Protocol, Type, TypeVar, Union, runtime_checkable

from sqlalchemy import Row, Sequence
from sqlalchemy.exc import DataError, SQLAlchemyError, UnboundExecutionError,InterfaceError, NoSuchModuleError
from sqlalchemy.orm.scoping import scoped_session

from ...database import Base

from ..core.exceptions import LayerError, layer_error_handler, translate_error


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

# class RepositoryRecordInvalid(RepositoryError):
#     valid_types = list(RecordTypes._value2member_map_)
#     default_message = f"Invalid record type provided! Value must be between {valid_types[0]} and {valid_types[-1]}."

REPOSITORY_ERROR_MAP = {
    (TimeoutError, UnboundExecutionError, InterfaceError, NoSuchModuleError): 
        (RepositoryConnectionError, False),
    (TypeError, KeyError, IndexError, ZeroDivisionError, DataError): (RepositoryParsingError, False),
    SQLAlchemyError: (RepositoryInternalError, False)
    
}

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


################################################
##  REPOSITORY CLASSES AND TYPES DEFINITIONS  ##
################################################

@runtime_checkable
class AsDictConvertible(Protocol):
    def _asdict(self) -> dict[str, Any]: ...
    @property
    def _mapping(self) -> dict[str, Any]: ...
    

ModelType = TypeVar("ModelType", bound=Base)

SingleResult = Union[ModelType, dict[str, Any]]
CollectionResult = Union[list[ModelType], list[dict[str, Any]]]
FlexibleResult = Union[SingleResult, CollectionResult]


def is_model_type(obj) -> bool:
    if ModelType.__bound__:
        return isinstance(obj, ModelType.__bound__)
    return True

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: scoped_session):
        if not issubclass(model, Base) or not model:
            raise RepositoryInvalidArgumentError(
                self.__class__.__name__,
                "__init__",
                f"Invalid model type: {type(model)}",
                True
            )
        self.model = model
        
        if session is None:
            raise RepositorySessionError()
        self.session = session
        
    @repository_error_handler()
    def get(self, pkey: int | str, to_dict=True) -> SingleResult:
        obj = self.session.get(self.model, pkey)
        
        if not obj:
            raise RepositoryNotFoundError(
                self.__class__.__name__, "get",
                f"Could not find row in {self.model} with a pkey = {pkey}", True  
            )
        
        return self.objs_to_dicts(obj) if to_dict else obj
    
    
    @repository_error_handler()
    def update(self, new_values: dict[ModelType, dict[str, Any]], to_dict=True) -> FlexibleResult:        
        # Return None if empty or undefined
        if not new_values:
            return []

        # Update all objects
        updated = []
        for obj, updates in new_values.items():
            # The object must be a correct type
            if not is_model_type(obj):
                raise RepositoryInvalidArgumentError(
                    self.__class__.__name__, "update",
                    "Object must be a valid model type!", True
                )
            
            # Now update all objs
            has_updated = False
            for key, new_value in updates.items():
                if not hasattr(obj, key):
                    raise RepositoryInvalidArgumentError(
                        self.__class__.__name__, "update",
                        f"Column name '{key}' not found in {obj}!", True
                    )
                
                current_value = getattr(obj, key)
                if current_value != new_value:
                    has_updated = True
                    setattr(obj, key, new_value)
            
            if has_updated:
                updated.append(obj)
        
        # Flush to reflect changes in session
        self.session.flush()
        
        updated = updated[0] if len(updated) == 1 else updated
        
        return self.objs_to_dicts(updated) if to_dict else updated
    
    
    @repository_error_handler()
    def update_with_pk(self, pkey: int | str, new_values: dict[str, Any], to_dict=True) -> SingleResult:
        obj = self.get(pkey, to_dict=False)
        return self.update({obj: new_values}, to_dict)
        
        
    @repository_error_handler()
    def create(self, new_data: list[dict[str, Any]], to_dict=True) -> CollectionResult:
        instances = [self.model(**data) for data in new_data]
        self.session.add_all(instances)
        self.session.flush()
        return self.objs_to_dicts(instances) if to_dict else instances
        
        
    @repository_error_handler()    
    def delete(self, value: int | str | ModelType) -> None:  
        obj = value if is_model_type(value) else self.get(value, to_dict=False)
        self.session.delete(obj)
        self.session.flush()
        
            
    @classmethod
    def objs_to_dicts(cls, values: AsDictConvertible | Sequence[AsDictConvertible]) -> dict[str, Any] | list[dict[str, Any]]:
        is_collection = isinstance(values, (Iterable))
        rows = values if is_collection else [values]
        
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
                    "objs_to_dicts",
                    "A provided does not contain functionality to map attributes to values!",
                    show_error=False
                )
                
        return results if is_collection else results[0]
        
