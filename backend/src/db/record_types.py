# An enumeration of train record types
from enum import Enum

from sqlalchemy.orm import Session

from .db_core.exceptions import RepositoryErrorInvoker
from .db_core.exceptions import RError as E
from .db_core.models import EOTCollation, EOTRecord, HOTCollation, HOTRecord
from .record_repo import RecordRepository


class RecordTypes(Enum):
    """
    An `Enum` representing the types of train records in the accessible in the application.

    Attributes:
        EOT (int): 1
        HOT (int): 2
        DPU (int): 3
    """
    
    EOT = 1
    HOT = 2
    DPU = 3
    
    @classmethod
    def error(cls) -> str:
        """Returns an error message specifying the valid value range for this enum when an invalid 
        record type is provided."""
        mapping = list(cls._value2member_map_)
        return f"Invalid record type provided! Value must be between {mapping[0]} and {mapping[-1]}."


class RecordFactory(RepositoryErrorInvoker):
    """Provides factory methods for initializing [`RecordRepository`][...record_repo.RecordRepository] 
    instances.
    
    Uses [`RepositoryErrorInvoker`][...db_core.exceptions.RepositoryErrorInvoker] for exception handling, 
    so this class must be initialized before use.
    
    Example:
        ```python
        >>> repo = RecordFactory().get_record_repository(1)
        >>> repo
        <__main__.RecordRepository object at 0x0000000000FFFFFF>
        ```
    """
    
    def get_record_repository(self, session: Session, value: int | RecordTypes) -> RecordRepository | None:
        """This method is used to instantiate a single 
        [`RecordRepository`][....record_repo.RecordRepository] instance.

        Given a `value` that corresponds to a valid train record type, a new
        [`RecordRepository`][....record_repo.RecordRepository] instance will be returned, including the 
        appropriate ORM model and collation types.

        Args:
            session (Session): An SQLAlchemy database session created by a Flask endpoint in
                which the new repository instance operates with.
            value (int | RecordTypes): An identifier that specifies the table/record type a
                [`RecordRepository`][....record_repo.RecordRepository] interacts with.

        Raises:
            RepositoryRecordInvalid: Raised if `value` is an invalid instance or does not
                    correspond to an appropriate train record type.

        Returns:
            (RecordRepository): A repository instance that queries type-specific train
                records. None if a record type should exist, but is not implemented yet.
        """
        if not isinstance(value, (int, RecordTypes)):
            self._raise(E.INVALID_RECORD, "Invalid record type provided! Value must be an int or enum value.", True)

        match value:
            case RecordTypes.EOT | RecordTypes.EOT.value:
                return RecordRepository(
                    EOTRecord, EOTCollation, session, "EOT Record", "eot"
                )
            case RecordTypes.HOT | RecordTypes.HOT.value:
                return RecordRepository(
                    HOTRecord, HOTCollation, session, "HOT Record", "hot"
                )
            case RecordTypes.DPU | RecordTypes.DPU.value:
                return None  # Not completed yet

        self._raise(E.INVALID_RECORD, RecordTypes.error(), True)


    def get_all_repositories(self, session: Session) -> list[RecordRepository]:
        """Returns a list of [`RecordRepository`][....record_repo.RecordRepository] 
        instances for every train/signal record type.

        Args:
            session (Session): An SQLAlchemy database session created by a Flask endpoint in
                which all new repository instances operate with.

        Returns:
            (list[RecordRepository]): A list of [`RecordRepository`][....record_repo.RecordRepository] 
                instances. Each repository corresponds to a train/signal record type. If a record type 
                does not have an implemented repository, it is not included in the returned list
                (ie. DPU).
        """

        valid_types = list(RecordTypes)
        repos = []
        
        for vt in valid_types:
            repo = self.get_record_repository(session, vt)
            # Only add if repo logic is implemented
            if repo is not None:
                repos.append(repo)
                
        return repos
