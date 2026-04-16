from collections.abc import Iterable
from typing import Any, Generic, Protocol, Type, TypeVar, Union, runtime_checkable

from sqlalchemy import Row, Sequence, inspect
from sqlalchemy.orm.session import Session

from .exceptions import (
    RepositoryInvalidArgumentError, RepositoryNotFoundError, RepositoryParsingError, 
    repository_error_handler
)
from .models import Base



@runtime_checkable
class AsDictConvertible(Protocol):
    """This protocol can be passed into a class to specify dictionary
    conversion capabilities."""
    def _asdict(self) -> dict[str, Any]: ...
    @property
    def _mapping(self) -> dict[str, Any]: ...
    
    
# A generic type variable in is constrained to only accept types that are subclasses of Base.
# Provides type safety by rejecting incompatible types at runtime.
ModelType = TypeVar("ModelType", bound=Base)

# Return type can be an ORM or dict instance
SingleResult = Union[ModelType, dict[str, Any]]
# Return type can be a list of ORMs or dicts
CollectionResult = Union[list[ModelType], list[dict[str, Any]]]
# Return type can be a single or a collection of result(s)
FlexibleResult = Union[SingleResult, CollectionResult]


class BaseRepository(Generic[ModelType]): 
    """Base class for a repository, supporting CRUD functionality for 
    SQLAlchemy ORMs. This class uses a generic, `ModelType`, which is bounded to 
    the `Base` class from `models`, defineing the model to operate on. Methods
    in this class return `ModelType`, but conversion to a `dict` as a return type 
    is supported if the provided model extends `Base`. 
    
    
    Args:
        Generic (ModelType): A type variable representing an SQLAlchemy ORM model 
            which extends `Base`. The model provdided defines which table to manipulate
            in a provided `Session`.
            
    Notes:
        - All methods in this class `flush` model changes in the session; however,
        these changes are not reflected in the database until a higher layer
        commits them.
    """
    
    def __init__(self, model: Type[ModelType], session: Session):
        """Constructor for a repository.
        
        Defines the model and `Session` that the repository operates on.
        If the model and session are valid, this instance maintains a reference
        to the model's primary key through `pkey`.
        

        Args:
            model (Type[ModelType]): _description_
            session (Session, optional): _description_. Defaults to None.
        """
        
        self.model = model
        self.session = session
        
        # Extract the primary key by inspecting the model's attributes
        self.pkey = None
        if self.model:
            pkeys = inspect(self.model).primary_key
            if pkeys:
                self.pkey = pkeys[0].name if pkeys else None
        
        
    @repository_error_handler()
    def get(self, pkey: Any, to_dict=True) -> SingleResult:
        """Retrieves an ORM from the session's current state. By default,
        this method returns a dictionary representation of the result, which 
        can be turned off by setting `to_dict` to `False`. A `RepositoryNotFoundError`
        will is thrown if the primary key cannot be found in the current session.

        Args:
            pkey (Any): Primary key to search for in the current session, typically
                an `int` or `str`.
                
            to_dict (bool, optional): Specifies whether retrieved instance should be
                returned as a `ModelType` or `dict`. Setting this field to `True` returns
                the results as a `dict`; otherwise, a `ModelType`. Default value is True.

        Raises:
            RepositoryNotFoundError: Thrown if the instance cannot be found in the current
                session with the provided `pkey`.

        Returns:
            SingleResult: A `ModelType` or `dict` instance of the result.
        """
        obj = self.session.get(self.model, pkey)
        
        # Throw error if row is not found
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
                    continue
                
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
        
            
    @repository_error_handler()
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
        
