# An enumeration of train record types
from enum import Enum

from .record_repo import RecordRepository
from .db_core.exceptions import RepositoryError
from .db_core.models import EOTRecord, EOTCollation, HOTRecord, HOTCollation


class RecordTypes(Enum):
    """An enum containing the types of train records in the application.

    Args:
        Enum: Enumerates the following values: `EOT = 1`, `HOT = 2`, `DPU = 3`.
    """
    
    EOT = 1
    HOT = 2
    DPU = 3


class RepositoryRecordInvalid(RepositoryError):
    """Raised when a invalid record type is provided to `get_record_repository`."""

    valid_types = list(RecordTypes._value2member_map_)
    default_message = f"Invalid record type provided! Value must be between {valid_types[0]} and {valid_types[-1]}."


def has_value(value: int):
    """Checks whether a provided value is a valid train record type.

    Args:
        value (int): The value to check.

    Raises:
        `RepositoryRecordInvalid`: Returned if `value` does not correspond to a train
                record type in the `RecordTypes` enum.

    Returns:
        bool: True if the value aligns with a valid record type; otherwise, false.
    """
    if not isinstance(value, int):
        raise RepositoryRecordInvalid(f"Expected int, got {type(value).__name__}")
    return any(value == item.value for item in RecordTypes)


def get_record_repository(session, value: int | RecordTypes) -> RecordRepository | None:
    """This function acts as a factory for instantiating a `RecordRepository`.

    Given a `value` that corresponds to a valid train record type, a new
    `RecordRepository` instance will be returned, including the appropriate ORM model
    and collation.

    Args:
        session (Session): An SQLAlchemy database session created by a Flask endpoint in
            which the new repository instance operates with.
        value (int | RecordTypes): An identifier that specifies the table/record type a
            `RecordRepository` interacts with.

    Raises:
        `RepositoryRecordInvalid`: Raised if `value` is an invalid instance or does not
                correspond to an appropriate train record type.

    Returns:
        RecordRepository: A repository instance that queries type-specific train
            records. None if a record type should exist, but is not implemented yet.
    """
    if not isinstance(value, (int, RecordTypes)):
        raise RepositoryRecordInvalid(value)

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

    raise RepositoryRecordInvalid(str(value))


def get_all_repositories(session) -> list[RecordRepository]:
    """Returns a list of `RecordRepository` instances for every train record type.

    Args:
        session (Session): An SQLAlchemy database session created by a Flask endpoint in
            which all new repository instances operate with.

    Returns:
        list[RecordRepository]: A list of `RecordRepository` instances with
            completed repository functionality.
    """

    valid_types = list(RecordTypes)
    repos = []
    
    for vt in valid_types:
        repo = get_record_repository(session, vt)
        # Only add if repo logic is implemented
        if repo is not None:
            repos.append(repo)
            
    return repos
