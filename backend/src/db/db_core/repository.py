from collections.abc import Iterable
from typing import Any, Generic, Protocol, Type, TypeVar, Union, runtime_checkable

from sqlalchemy import Row, Sequence, inspect
from sqlalchemy.orm.session import Session

from .exceptions import (
    RepositoryInvalidArgumentError, RepositoryNotFoundError, RepositoryParsingError, 
    repository_error_handler
)
from .models import Base


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


class BaseRepository(Generic[ModelType]): 
    def __init__(self, model: Type[ModelType], session: Session = None):
        self.model = model
        self.session = session
        
        self.pkey = None
        if self.session is not None:
            pkeys = inspect(self.model).primary_key
            self.pkey = pkeys[0].name
        
        
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
    def update(self, objs: list[tuple[ModelType, dict[str, Any]]], to_dict=True) -> CollectionResult:        
        # Return None if empty or undefined
        if not objs:
            return []

        # Update all objects
        updated = []
        for obj, updates in objs:
            # The object must be a correct type
            if not issubclass(obj.__class__, Base):
                raise RepositoryInvalidArgumentError(
                    self.__class__.__name__, "update",
                    "Object must be a valid model instance!", True
                )
            
            # Now update all objs
            has_updated = False
            for key, new_value in updates.items():
                if key == self.pkey:
                    raise RepositoryInvalidArgumentError(
                        self.__class__.__name__, "update",
                        f"Cannot update {self.pkey}!", True
                    )
                
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
        
        return self.objs_to_dicts(updated) if to_dict else updated
    
    
    @repository_error_handler()
    def update_with_pk(self, pkey: int | str, new_values: dict[str, Any], to_dict=True) -> SingleResult | None:
        obj = self.get(pkey, to_dict=False)
        result = self.update([(obj, new_values)], to_dict)
        return result[0] if len(result) == 1 else None
        
        
    @repository_error_handler()
    def create(self, new_data: list[dict[str, Any]] | dict[str, Any], to_dict=True) -> CollectionResult:
        instances = (
            [self.model(**data) for data in new_data] 
            if isinstance(new_data, list) else
            [self.model(**new_data)]
        )
        self.session.add_all(instances)
        self.session.flush()     
           
        return self.objs_to_dicts(instances) if to_dict else instances
        
        
    @repository_error_handler()    
    def delete(self, value: int | str | ModelType) -> None:  
        obj = value if issubclass(value.__class__, Base) else self.get(value, to_dict=False)
        self.session.delete(obj)
        self.session.flush()
        
            
    @classmethod
    def objs_to_dicts(cls, values: AsDictConvertible | Sequence[AsDictConvertible], convert_to_string: set[str] = {}) -> dict[str, Any] | list[dict[str, Any]]:
        # Determine if the values given is iterable
        is_collection = isinstance(values, (Iterable))
        rows = values if is_collection else [values]

        results = []
        for r in rows:
            # If the row is an SQLAlchemy Row or Iterable and contains one instance, then retrieve the first index
            if isinstance(r, (Row, Iterable)) and len(r) == 1:
                row = r[0]
            # Otherwise, convert the entire row
            else:
                row = r
            
            # Check to see if the row can be converted into a dictionary
            if hasattr(row, "_mapping"):
                results.append(dict(row._mapping))
            elif hasattr(row, "_asdict"):
                results.append(row._asdict())
            else:
                try:
                    results.append(dict(row))
                # Raise an exception if the row cannot be converted
                except:
                    raise RepositoryParsingError(
                        cls.__name__,
                        "objs_to_dicts",
                        "A provided instance does not contain functionality for dictionary conversion!",
                        show_error=False
                    )
        
        # Convert any values if corresponding keys should be converted to a string
        if len(convert_to_string) > 0:
            for d in results:
                d.update({k: str(d[k]) for k in convert_to_string if k in d})
                
        return results if is_collection else results[0]
        
