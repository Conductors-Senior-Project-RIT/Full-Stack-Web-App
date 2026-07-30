from datetime import datetime
from math import ceil
from typing import Any, Generic, Optional, TypeVar

from sqlalchemy import func, inspect, select, text, update
from sqlalchemy.orm.session import Session

from .db_core.exceptions import RepositoryErrorHandler, RError
from .db_core.models import BaseRecord, CollationMixin
from .db_core.repository import BaseRepository

# Define the type of models accepted by this class
RecordType = TypeVar("RecordType", bound=BaseRecord)
CollationType = TypeVar("CollationType", bound=CollationMixin)

class RecordRepository(BaseRepository[RecordType], Generic[RecordType]):
    """A database interface for train record querying.

    This class inherits the generic CRUD functionality defined in 
    [`BaseRepository`][...db_core.repository.BaseRepository], which is 
    useful for simple operations. It contains concrete methods which execute 
    standardized functionality using the model defined in an instance, 
    restricted only to models that extend [`BaseRecord`][...db_core.models.BaseRecord].

    This class is generic over [`RecordType`][types-record], which must be bound to models 
    that extend [`BaseRecord`][...db_core.models.BaseRecord].
    """

    def __init__(
        self,
        model: type[BaseRecord],
        collation: type[CollationMixin],
        session: Session,
        record_name: str = "Unknown",
        record_identifier: str = "Unknown",
    ):
        """Constructor for a repository that interacts with various kinds of train records.

        Both the `model` and `collation` parameters must be assigned to classes that extend 
        [`BaseRecord`][....db_core.models.BaseRecord] and [`CollationMixin`][....db_core.models.CollationMixin], 
        respectively. It is also important to note that the `session` passed in is typically a 
        `scoped_session` (see SQLAlchemy docs) created by *Flask*. All methods that make changes 
        to the database are flushed in the session. It is the responsibility of the higher layers 
        to commit these changes upon success.
        
        Additionally, both the `record_name` and `record_identifier` are used in some of
        the queries. To get an idea of what they are used for, see 
        [`get_records_at_station`][..get_records_at_station].

        See [`record_types`][....record_types] for factory method implementations.

        Args:
            model (BaseRecord): An ORM class that defines what database table to
                perform queries on and map results to. Only models that extend
                [`BaseRecord`][....db_core.models.BaseRecord] are permitted.
            collation (CollationMixin): An ORM model that defines the attributes
                of the results returned by [`get_record_collation`][..get_record_collation].
                Only models that extend [`CollationMixin`][....db_core.models.CollationMixin] 
                are permitted.
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

    @RepositoryErrorHandler.layer_error_decorator()
    def get_total_record_count(self) -> int:
        """Retrieves total number of records present in the table for a given session.

        Returns:
            (int): Number of records present in the provided table defined by `model`.
        """
        return self.session.query(func.count(self.model.id)).scalar()


    def get_train_history(self, record_id: int) -> dict[str, Any]:
        """Returns a train record with the following columns: `id, date_rec, station_name,
        symb_name, unit_addr, verified` and the columns defined in a concrete model's
        [`get_unique_fields`][src.db.db_core.models.BaseRecord.get_unique_fields] method.

        Args:
            record_id (int): A value corresponding to a record's primary key.

        Returns:
            (dict[str, Any]): Returns a dictionary containing the fields and corresponding
                values for a train record.
        """
        from .db_core.models import Station, Symbol
        
        try:
            # Include the columns that will be present in the results across all records
            columns = [
                self.model.id,
                func.to_char(self.model.date_rec, "YYYY-MM-DD HH24:MI:SS").label(
                    "date_rec"
                ),
                Station.station_name,
                Symbol.symb_name,
                self.model.unit_addr,
                self.model.verified
            ]

            # Extend to get model specific records columns
            columns.extend(self.model.get_unique_fields())

            stmt = (
                select(*columns)
                .join(Station, Station.id == self.model.station_recorded)
                .outerjoin(Symbol, Symbol.id == self.model.symbol_id)
                .where(self.model.id == record_id)
            )

            results = self.session.execute(stmt).one()
            return self.objs_to_dicts(results)
        
        except Exception as e:
            self._translate_and_raise(e, f"Could not get record with ID = {record_id}!")

    @RepositoryErrorHandler.layer_error_decorator()
    def create_train_record(
        self, args: dict[str, Any], datetime_received: datetime
    ) -> tuple[int, bool]:
        """Creates a new train record with the provided values in `args`.

        When an error occurs during the initial creation of a record, a recovery request
        can be sent. When a recovery request is sent, the datetime must be passed as a
        parameter; otherwise, a [`RepositoryInvalidArgumentError`][error-types] 
        is raised. In order to successfully create a new train record, the keys and values 
        in the dictionary must include all non-nullable columns and correct value types with 
        that of the model to prevent an `IntegrityError` occurring. Keys not present in the 
        model are ignored.

        Args:
            args (dict[str, Any]): A dictionary containing values to insert into a new
                record.
            datetime_received (datetime): The datetime when the record was received.

        Returns:
            (tuple[int, bool]): The id of the newly created record, and whether a recovery
                request was initiated.
        """
        recovery_request = True

        # Get only the columns actually mapped on the concrete model
        mapper = inspect(self.model)
        mapped_keys = {attr.key for attr in mapper.mapper.columns}

        sql_args = {}
        for key, value in args.items():
            if key in mapped_keys:
                sql_args[key] = value

        # If the datetime a record was received is not passed in 'args', add 'datetime_string' into the dictionary.
        if sql_args["date_rec"] is None:
            self._validate(
                condition=datetime_received is not None, 
                error_class=RError.INVALID_ARG, 
                message="Record timestamp must be provided!", 
                show_error=True
            )

            sql_args["date_rec"] = datetime_received
            # Indicate that a recovery request was not initiated
            recovery_request = False
        else:
            sql_args["date_rec"] = datetime.fromisoformat(sql_args["date_rec"])

        result = self.create(sql_args, False)  # Already flushes

        # Should not happen if args contains items
        self._validate(
            condition=result is not None, 
            error_class=RError.INTERNAL, 
            message="Could not create new train record, 0 rows created!", 
            show_error=True
        )

        # The 'create' function returns a list of ORM instances, access the first index since only one record is created
        return result[0].id, recovery_request

    @RepositoryErrorHandler.layer_error_decorator()
    def get_unit_record_ids(self, unit_addr: str, recent=False) -> int | list[int]:
        """Queries the database session and the model defined in the constructor
        for all record IDs matching the specified unit address, ordered ascending by ID. 
        Optionally returns only the most recent (greatest) ID.

        Args:
            unit_addr (str): The unit address used to filter records.
            recent (bool): If True, returns only the most recent record ID. Defaults to
                False.

        Returns:
            (int | list[int]): A single integer ID if `recent=True`, or a list of all
                matching integer IDs if `recent=False`.

        Raises:
            RepositoryNotFoundError: If no records are found for the given
                    `unit_addr`.
        """

        stmt = (
            select(self.model.id)
            .where(self.model.unit_addr == unit_addr)
            .order_by(self.model.id.asc())
        )
        result = self.session.execute(stmt).scalars().all()

        self._validate(
            condition=result is not None and len(result) > 0, 
            error_class=RError.NOT_FOUND, 
            message=f"Failed to get record ID where the unit address = {unit_addr}", 
            show_error=True
        )

        # Since we are ordering by ascending order, the most recent record is at the end.
        return result[-1] if recent else result


    @RepositoryErrorHandler.layer_error_decorator()
    def get_recent_trains(self, unit_addr: str, station_id: int, id_only: bool = True) -> list[dict]:
        """Queries the database session and the model defined in the constructor 
        for all records matching the specified unit address and station ID where the recorded date 
        is within the last 10 minutes.

        Args:
            unit_addr (str): The unit address used to filter records.
            station_id (int): The station ID used to filter records.
            id_only (bool): If True, returns only the IDs of the matching records. Defaults to False.

        Returns:
            (list[dict]): A list of matching train records as dictionaries. Returns an
                empty list if no records are found.
        """
        # Select only IDs if specified, otherwise select all columns to return as dictionaries
        stmt = select(self.model.id) if id_only else select(self.model)

        # Receive records from the last ten minutes
        stmt = stmt.where(
            self.model.unit_addr == unit_addr,
            self.model.station_recorded == station_id,
            self.model.date_rec >= func.now() - text("INTERVAL '10 minutes'"),
        )

        results = self.session.execute(stmt).scalars().all()
        return list(results) if id_only else self.objs_to_dicts(results)


    @RepositoryErrorHandler.layer_error_decorator()
    def add_new_pin(self, record_id: int, unit_addr: str) -> list[int]:
        """Sets `most_recent` to false for all most recent records with matching unit
        addresses and IDs not matching `record_id`.

        Args:
            record_id (int): The record ID that is excluded from update.
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

    @RepositoryErrorHandler.layer_error_decorator()
    def get_record_column_by_unit_addr(
        self, unit_addr: str, field_type: str, most_recent: Optional[bool] = None
    ) -> list[Any]:
        """Gets the values for each record with matching unit addresses for a given 
        column name.

        Args:
            unit_addr (str): The unit address used to filter records.
            field_type (str): The column name to retrieve values from.
            most_recent (bool | None, optional): Filters records by their recency. If
                None, all records will be scanned. Defaults to None.

        Raises:
            RepositoryInvalidArgumentError: Raised if the model does not contain the
                    provided field.

        Returns:
            (list[Any]): Returns a list of values from records.
        """
        # Check if the provided column actually exists in the model
        self._validate(
            condition=hasattr(self.model, field_type), 
            error_class=RError.INVALID_ARG, 
            message=f"Column '{field_type}' not found in {self.model.__name__}!", 
            show_error=True
        )

        stmt = (
            select(getattr(self.model, field_type))
            .where(self.model.unit_addr == unit_addr)
            .order_by(self.model.id.asc())
        )

        if most_recent is not None:
            stmt = stmt.where(self.model.most_recent == most_recent)

        return self.session.execute(stmt).scalars().all()

    @RepositoryErrorHandler.layer_error_decorator()
    def update_signal_values(
        self, record_id: int, symbol_id: int, engine_num: int
    ) -> dict[str, Any] | None:
        """Updates a record's `symbol_id` and `engine_num` with a matching ID.

        This method ignores new values with invalid types such that they will not
        be reflected in the database session.

        Args:
            record_id (int): The ID of the record to update.
            symbol_id (int): The new symbol ID value.
            engine_num (int): The new engine number value.

        Returns:
            (dict[str, Any] | None): Returns a dictionary containing the newly updated
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
    ) -> tuple[list[dict], int]:
        """Retrieves a paginated collation of train records grouped by unit address and
        station.

        Executes a multi-stage SQL query that groups train records by unit address and
        station, where a new group is formed when either the station changes or a
        duration of more than 2 hours elapses between records. Returns the most recent
        record per group along with aggregate information such as `first_seen`,
        `last_seen`, `occurrence_count`, and `duration`. The total count of grouped
        records for pagination is appended to each collation result and can be accessed
        via `total_count` (see the collation ORMs in [`db_core.models`][....db_core.models.CollationMixin] 
        for more details). Optionally filters results by verification status if provided.

        This function uses collation views to query results which should already be
        added to the Tracksense PostgreSQL database server. However, it can be found in
        `backend/test/table.sql` if it is removed for any reason.

        Args:
            page (int): The page number (offset) to retrieve, 1-indexed.
            num_results (int): The number of results to return per page.
            verified (bool | None): If True or False, filters records by their
                `verified` status. If None, no filter is applied. Defaults to None.

        Returns:
            [tuple[list[dict], int]]: A tuple containing: 
                
                - `list`: The paginated and collated train records as dictionaries. 
                - `int`: The total number of pages based on `num_results`.

        Raises:
            RepositoryError: If any stage of the query, count, or result parsing
                    fails.
        """
        try:
            # Construct the statement via a PSQL view defined by the collation ORM
            stmt = select(self.collation)

            if verified is not None:
                stmt = stmt.where(self.collation.verified == verified)

            # Additional filters to limit the results on a page, and offset based on the page specified
            stmt = (
                stmt.order_by(self.collation.date_rec.desc())
                .limit(num_results)
                .offset((page - 1) * num_results)
            )

            results = self.session.execute(stmt).scalars().all()

            # By returning scalars, collation instances are returned, which contain the total number of results
            count = results[0].total_count if results else 0
            
            # Convert `duration` and `occurrence_count` to strings manually
            records = self.objs_to_dicts(results, {"duration", "occurrence_count"})
            total_pages = ceil(count / num_results)

            return records, total_pages

        except Exception as e:
            self._translate_and_raise(e, f"Error collating {self.record_identifier.upper()} records!")


    def verify_record(
        self, record_id: int, symbol_id: int, locomotive_num: str | None
    ) -> dict[str, Any] | None:
        """Verifies a record by updating its symbol ID, locomotive number, and verified
        status.

        Sets `verified` to True on the specified record along with the provided
        `symbol_id` and `locomotive_num` values. Uses 
        [`update_with_pk`][src.db.db_core.repository.BaseRepository.update_with_pk] to flush 
        changes to the session.

        Args:
            record_id (int): The ID of the record to verify.
            symbol_id (int): The updated symbol ID of the record.
            locomotive_num (str | None): The updated locomotive number of the record.

        Returns:
            (dict[str, Any]): The updated record as a dictionary representation. None, if
                no updates were made in the session.

        Raises:
            RepositoryError: If an exception occurs for any reason.
        """
        try:
            values = {"verified": True}
            
            if symbol_id > 0:
                values["symbol_id"] = symbol_id
            if locomotive_num is not None:
                values["locomotive_num"] = locomotive_num

            return self.update_with_pk(record_id, values)  # Already flushes

        except Exception as e:
            self._translate_and_raise(e, f"Could not verify {self.record_name} {record_id}")


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

        Joins with [`Station`][....db_core.models.Station] and [`Symbol`][....db_core.models.Symbol] 
        to include the station and symbol name references in the returned records. A record's `Data_type` 
        field, which is derived from a repository's `record_identifier`, is appended to each result.

        Args:
            station_id (int, optional): The station ID to filter records by. Pass -1 to
                retrieve records across all stations. Defaults to -1.
            dt (datetime, optional): A lower bound datetime instance to filter records
                by `date_rec`. Defaults to None.
            recent (bool, optional): If True or False, filters records by their
                `most_recent` value. If None, no filter is applied. Defaults to None.
            all_cols (bool, optional): If True, all columns of a record are returned; 
                otherwise, only a portion are returned. Defaults to False.

        Returns:
            (list[dict[str, Any]]): A list of matching records as dictionaries, each
                containing `id`, `unit_addr`, `date_rec`, `station_name`, `symb_name`,
                `engine_num`, `locomotive_num`, and `Data_type`. Returns an empty list
                if no records are found.

        Raises:
            RepositoryError: If an exception is raised for any reason.
        """
        # We need to query from two different tables, so import them in the function
        # to prevent unecessarily flooding the namespace or circular imports.
        from .db_core.models import Station, Symbol

        try:
            # Station name and symbol name always included
            cols = [Station.station_name, Symbol.symb_name]
            
            # Retrieve all of a model's columns if requested, otherwise just return a subset of them
            if all_cols:
                mapper = inspect(self.model)
                cols.extend(
                    [getattr(self.model, c.key) for c in mapper.mapper.column_attrs]
                )
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

            # Build the list of filters based on the provided parameters
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

            results = self.objs_to_dicts(self.session.execute(stmt).all())

            # Add data type to result (used for front-end purposes)
            for result in results:
                result["Data_type"] = self.record_identifier.upper()

            return results

        except Exception as e:
            self._translate_and_raise(e, f"Could not retrieve {self.record_name}s at station{f' {station_id}' if station_id != -1 else 's'}!")
