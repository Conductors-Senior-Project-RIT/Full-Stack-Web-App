from datetime import datetime
from math import ceil
from typing import Any, Generic, Optional, TypeVar
from sqlalchemy import func, select, text, update
from sqlalchemy.orm.session import Session

from .db_core.models import BaseRecord, CollationMixin
from .db_core.repository import BaseRepository
from .db_core.exceptions import (
    RepositoryError,
    RepositoryInternalError,
    RepositoryNotFoundError,
    RepositoryInvalidArgumentError,
    repository_error_handler,
    repository_error_translator,
)


# Define the type of models accepted by this class
RecordType = TypeVar("RecordType", bound=BaseRecord)
CollationType = TypeVar("CollationType", bound=CollationMixin)


class RecordRepository(BaseRepository[RecordType], Generic[RecordType]):
    """A database interface for train record querying.

    This class inherits the generic CRUD functionality defined in `BaseRepository` that
    may be useful for simple operations. Additionally, this abstract class contains
    concrete methods which execute standardized functionality using the model defined by
    a child class, restricted only to models that extend `BaseRecord`. Additionally,
    this class also defines abstract methods which must be implmeneted by child classes.

    Args:
        ABC: This class is abstract and cannot be instantiated. A child class can extend
            `BaseRepository` for a concrete implementation.
        BaseRepository (RecordType): Inherits the methods present in `BaseRepository`
            which operate on `RecordType` models.
        Generic (RecordType): Defines the `RecordType` model for a repository instance.
    """

    def __init__(
        self,
        model: RecordType,
        collation: CollationType,
        session: Session,
        record_name: str = "Unknown",
        record_identifier: str = "Unknown",
    ):
        """Constructor for a repository that interacts with different train records.

        See `record_types` for factory method implementations.

        Args:
            model (RecordType): An ORM class that defines what database table to perform
                queries on. Only models that extend the `BaseRecord` are permitted.
            session (Session): Specifies the database session the repository operates
                in. All functions in this class flushes all changes to the session. It
                is the job of higher layers to commit or rollback any changes.
            record_name (str, optional): Attributes a name to the records in the
                repository. Primarily for error logging purposes. Defaults to "Unknown".
            record_identifier (str, optional): Attributes a unique identifer for records
                in the repository. Particularly useful when parsing data. Defaults to
                "Unknown".
        """
        super().__init__(model, session)
        self.collation = collation
        self.record_name = record_name
        self.record_identifier = record_identifier

    @repository_error_handler()
    def get_total_record_count(self) -> int:
        """Retrieves total number of records present in the table during a given session.

        Returns:
            int: Number of records present in `model` (`RecordType`).
        """
        return self.session.query(func.count(self.model.id)).scalar()

    def get_train_history(self, record_id: int) -> list[dict[str, Any]]:
        """Returns a train record with the specified columns, defined in the concrete
        implementation.

        Args:
            record_id (int): A value corresponding to a record's primary key.

        Returns:
            dict[str, Any]: Returns a dictionary containing the fields and corresponding
                values for a train record.
        """
        from .db_core.models import Station, Symbol

        columns = [
            self.model.id,
            func.to_char(self.model.date_rec, "YYYY-MM-DD HH24:MI:SS").label(
                "date_rec"
            ),
            Station.station_name,
            Symbol.symb_name,
            self.model.unit_addr,
            self.model.verified,
        ]

        columns.extend(self.model.get_unique_fields())

        stmt = (
            select(*columns)
            .join(Station, Station.id == self.model.station_recorded)
            .outerjoin(Symbol, Symbol.id == self.model.symbol_id)
            .where(self.model.id == record_id)
        )
  
        results = self.session.execute(stmt).one_or_none()
        return self.objs_to_dicts(results)

    @repository_error_handler()
    def create_train_record(
        self, args: dict[str, Any], datetime_string: str | None
    ) -> tuple[int, bool]:
        """Creates a new train record with the provided values in `args`.

        When an error occurs during the initial creation of a record, a recovery request
        can be sent. When a recovery request is sent, the datetime must be passed as a
        parameter; otherwise, a `RepositoryInvalidArgumentError` is raised. In order to
        successfully create a new train record, the keys and values in the dictionary
        must include all non-nullable columns and correct value types with that of the
        model to prevent an `IntegrityError` occurring. Keys not present in the model
        are ignored.

        Args:
            args (dict[str, Any]): A dictionary containing values to insert into a new
                record.
            datetime_string (str): String representing when the record was received.
                Must match the following format: `%Y-%m-%d %H:%M:%S`.

        Returns:
            tuple[int, bool]: The id of the newly created record, and whether a recovery
                request was initiated.
        """
        recovery_request = True

        # Check to see if any of the keys in the 'args' dict aren't a column in the table
        sql_args = {}
        for key, value in args.items():
            if hasattr(self.model, key):
                sql_args[key] = value

        # If the datetime a record was received is not passed in 'args', add 'datetime_string' into the dictionary.
        if sql_args["date_rec"] is None:
            if datetime_string is None:
                raise RepositoryInvalidArgumentError(
                    self.__class__.__name__,
                    message="Record timestamp must be provided!",
                    show_error=True,
                )

            sql_args["date_rec"] = datetime_string
            recovery_request = (
                False  # Indicate that a recovery request was not initiated
            )

        result = self.create(sql_args, False)  # Already flushes

        # Should not happen if args contains items
        if not result:
            raise RepositoryInternalError(
                caller_name=self.__class__.__name__,
                message="Could not create new train record, 0 rows created!",
                show_error=True,
            )

        # The 'create' function returns a list of ORM instances, access the first index since only one record is created
        return result[0].id, recovery_request

    @repository_error_handler()
    def get_unit_record_ids(self, unit_addr: str, recent=False) -> int | list[int]:
        """Retrieves record IDs associated with a given unit address.

        Queries the database session for all record IDs matching the specified unit
        address, ordered ascending by ID. Optionally returns only the most recent
        (highest) ID.

        Args:
            unit_addr (str): The unit address used to filter records.
            recent (bool): If True, returns only the most recent record ID. Defaults to
                False.

        Returns:
            int | list[int]: A single integer ID if `recent=True`, or a list of all
                matching integer IDs if `recent=False`.

        Raises:
            `RepositoryNotFoundError`: If no records are found for the given
                    `unit_addr`.
        """

        stmt = (
            select(self.model.id)
            .where(self.model.unit_addr == unit_addr)
            .order_by(self.model.id.asc())
        )
        result = self.session.execute(stmt).scalars().all()

        if not result:
            raise RepositoryNotFoundError(
                caller_name=self.__class__.__name__,
                message=f"Could not get record ID where the unit address = {unit_addr}",
                show_error=False,
            )

        # Since we are ordering by ascending order, the most recent record is at the end.
        return result[-1] if recent else result

    @repository_error_handler()
    def get_recent_trains(self, unit_addr: str, station_id: int) -> list[dict]:
        """Retrieves train records from the last 10 minutes for a given unit and station.

        Queries the database session for all records matching the specified unit address
        and station ID where the recorded date is within the last 10 minutes.

        Args:
            unit_addr (str): The unit address used to filter records.
            station_id (int): The station ID used to filter records.

        Returns:
            list[dict]: A list of matching train records as dictionaries. Returns an
                empty list if no records are found.
        """

        # Receive records from the last ten minutes
        stmt = select(self.model).where(
            self.model.unit_addr == unit_addr,
            self.model.station_recorded == station_id,
            self.model.date_rec >= func.now() - text("INTERVAL '10 minutes'"),
        )

        results = self.session.execute(stmt).all()
        return self.objs_to_dicts(results)

    @repository_error_handler()
    def add_new_pin(self, record_id: int, unit_addr: str) -> list[int]:
        """Sets the most recent column for a group of records with matching unit addresses.

        Sets `most_recent` to false for all most recent records with matching unit
        addresses with distinct IDs.

        Args:
            record_id (int): The record ID that is excluded from search.
            unit_addr (str): The unit address used to filter records.

        Returns:
            list[int]: Returns a list of IDs of the records that were updated.
        """

        stmt = (
            update(self.model)
            .where(
                self.model.id != record_id,
                self.model.unit_addr == unit_addr,
                self.model.most_recent.is_(True),
            )
            .values(most_recent=False)
            .returning(self.model.id)
        )

        # Returns the IDs of the newly updated records
        result = self.session.execute(stmt).scalars().all()

        # Flush the new changes to be reflected in the current session
        self.session.flush()

        return result

    @repository_error_handler()
    def get_record_column_by_unit_addr(
        self, unit_addr: str, field_type: str, most_recent: Optional[bool] = None
    ) -> list[Any]:
        """Gets the values for each record with matching unit addresses for a given field.

        Args:
            unit_addr (str): The unit address used to filter records.
            field_type (str): The column name to retrieve values from.
            most_recent (bool | None, optional): Filters records by their recency. If
                None, all records will be scanned. Defaults to None.

        Raises:
            `RepositoryInvalidArgumentError`: Raised if the model does not contain the
                    provided field.

        Returns:
            list[Any]: Returns a list of values from records.
        """
        # Check if the provided column actually exists in the model
        if not hasattr(self.model, field_type):
            raise RepositoryInvalidArgumentError(
                self.__class__.__name__,
                f"Column '{field_type}' not found in {self.model.__name__}!",
                True,
            )

        stmt = (
            select(getattr(self.model, field_type))
            .where(self.model.unit_addr == unit_addr)
            .order_by(self.model.id.asc())
        )

        # Add the "where" component if looking for specific value
        if most_recent is not None:
            stmt = stmt.where(self.model.most_recent == most_recent)

        return self.session.execute(stmt).scalars().all()

    @repository_error_handler()
    def update_signal_values(
        self, record_id: int, symbol_id: int, engine_num: int
    ) -> dict[str, Any] | None:
        """Updates a record's `symbol_id` and `engine_num` with a matching ID.

        The values passed in must be of the correct type to prevent an `IntegrityError`.
        Fields with invalid types or values will not be reflected in the database
        session.

        Args:
            record_id (int): The ID of the record to update.
            symbol_id (int): The new symbol ID value.
            engine_num (int): The new engine number value.

        Returns:
            dict[str, Any] | None: Returns a dictionary containing the newly updated
                values. Returns None if no updates were made in the session.
        """

        values = {}
        if isinstance(symbol_id, int) and symbol_id > 0:
            values["symbol_id"] = symbol_id
        if isinstance(engine_num, int) and engine_num > 0:
            values["engine_num"] = engine_num

        return self.update_with_pk(record_id, values)  # Already flushes

    def get_record_collation(
        self, page: int, num_results: int, verified: Optional[bool] = None
    ) -> dict[str, list | int]:
        """Retrieves a paginated collation of train records grouped by unit address and
        station.

        Executes a multi-stage SQL query that groups train records by unit address and
        station, where a new group is formed when either the station changes or a
        duration of more than 2 hours occurs between records. Returns the most recent
        record per group along with aggregate details such as `first_seen`, `last_seen`,
        `occurrence_count`, and `duration`. A second query retrieves the total count of
        grouped records for pagination. Optionally filters results by verification
        status if provided.

        Args:
            page (int): The page number to retrieve, 1-indexed.
            num_results (int): The number of results to return per page.
            verified (bool | None): If True or False, filters records by their
                `verified` status. If None, no filter is applied. Defaults to None.

        Returns:
            dict[str, list | int]: A dictionary containing: - `results` (list): The
                paginated and collated train records as dictionaries. - `totalPages`
                (int): The total number of pages based on `num_results`.

        Raises:
            `RepositoryError`: If any stage of the query, count, or result parsing
                    fails.
        """
        try:
            stmt = select(self.collation)

            if verified is not None:
                stmt = stmt.where(self.collation.verified == verified)

            stmt = (
                stmt.order_by(self.collation.date_rec.desc())
                .limit(num_results)
                .offset((page - 1) * num_results)
            )

            results = self.session.execute(stmt).scalars().all()
            count = results[0].total_count if results else 0
            
            if count == 0:
                raise RepositoryNotFoundError(
                    self.__class__.__name__,
                    message=f"Could not find any records on page {page}!",
                    show_error=True
                )

            return {
                "results": self.objs_to_dicts(
                    results, {"duration", "occurrence_count"}
                ),
                "totalPages": ceil(count / num_results),
            }

        except Exception as e:
            raise repository_error_translator(
                e,
                self.__class__.__name__,
                message=f"Error collating {self.record_identifier.upper()} records: {e}",
                exclude=RepositoryError,
            )

    def verify_record(
        self, record_id: int, symbol_id: int, locomotive_num: str
    ) -> dict[str, Any]:
        """Verifies a record by updating its symbol ID, locomotive number, and verified
        status.

        Sets `verified` to True on the specified record along with the provided
        `symbol_id` and `locomotive_num` values. Uses `update_with_pk` in
        `BaseRepository` to flush changes to the session.

        Args:
            record_id (int): The primary key of the record to verify.
            symbol_id (int): The updated symbol ID of the record.
            locomotive_num (str): The updated locomotive number of the record.

        Returns:
            dict[str, Any]: The updated record as a dictionary representation.

        Raises:
            `RepositoryError`: If an exception occurs for any reason.
        """
        try:
            # Assign a new symbol and locomotive number to a newly verified record if provided.
            values = {
                "symbol_id": symbol_id,
                "locomotive_num": locomotive_num,
                "verified": True,
            }

            return self.update_with_pk(record_id, values)  # Already flushes

        except Exception as e:
            raise repository_error_translator(
                e,
                self.__class__.__name__,
                None,
                f"Could not verify {self.record_name} {record_id}: {e}",
            )

    # Time frame
    def get_records_at_station(
        self,
        station_id: Optional[int] = -1,
        dt: Optional[datetime] = None,
        recent: Optional[bool] = None,
        all_cols: bool = False,
    ) -> list[dict[str, Any]]:
        """Retrieves records with the station they were recorded at.

        Records can be filtered based on the station they were recorded by passing a
        matching `station_id`. If `station_id` is `-1`, the station filter is not
        applied and will return records across all stations. When `dt` is provided, the
        database is queried to filter all records with a `date_rec` at or after `dt`. If
        a value is passed for `recent`, the records will be filtered with their matching
        recency status.

        If `all_cols` is `False`, only the following columns are retrieved: `id,
        unit_addr, date_rec, station_name, symb_name, engine_num, locomotive_num`;
        otherwise, every column in a record is retrieved, including the corresponding
        `symb_name` and `station_name`.

        The query used, joins with `Station` and `Symbol` to include the station and
        symbol name references in the returned records. A record's `Data_type` field,
        which is derived from a repository's `record_identifier`, is appended to each
        result.

        Args:
            station_id (int, optional): The station ID to filter records by. Pass -1 to
                retrieve records across all stations. Defaults to -1.
            dt (datetime, optional): A lower bound datetime instance to filter records
                by `date_rec`. Defaults to None.
            recent (bool, optional): If True or False, filters records by their
                `most_recent` value. If None, no filter is applied. Defaults to None.
            all_cols (bool): If True, all columns of a record are returned; otherwise,
                only a portion are returned.

        Returns:
            list[dict[str, Any]]: A list of matching records as dictionaries, each
                containing `id`, `unit_addr`, `date_rec`, `station_name`, `symb_name`,
                `engine_num`, `locomotive_num`, and `Data_type`. Returns an empty list
                if no records are found.

        Raises:
            `RepositoryError`: If an exception is raised for any reason.
        """
        # We need to query from two different tables, so import them in the function
        # to prevent unecessarily flooding the namespace or circular imports.
        from .db_core.models import Symbol, Station

        try:
            cols = [Station.station_name, Symbol.symb_name]
            if all_cols:
                cols.extend([self.model])
            else:
                cols.extend(
                    [
                        self.model.id,
                        self.model.unit_addr,
                        self.model.date_rec,
                        self.model.engine_num,
                        self.model.locomotive_num,
                    ]
                )

            filters = []
            if dt is not None:
                filters.append(self.model.date_rec >= dt)

            if station_id != -1:
                filters.append(Station.id == station_id)

            if recent is not None:
                filters.append(self.model.most_recent == recent)

            stmt = (
                select(*cols)
                .join(Station, self.model.station_recorded == Station.id)
                .outerjoin(Symbol, self.model.symbol_id == Symbol.id)
                .where(*filters)
                .order_by(self.model.date_rec.desc())
            )

            to_str = {"date_rec"} if all_cols else {}
            results = self.objs_to_dicts(self.session.execute(stmt).all(), to_str)

            # Add data type to result
            for result in results:
                result["Data_type"] = self.record_identifier.upper()

            return results

        except Exception as e:
            raise repository_error_translator(
                e,
                self.__class__.__name__,
                None,
                f"Could not retrieve {self.record_name}s at station{f' {station_id}' if station_id != -1 else 's'}: {e}",
            )
