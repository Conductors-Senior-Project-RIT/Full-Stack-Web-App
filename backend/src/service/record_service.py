import datetime
import sys
from typing import Any, Optional
import zoneinfo

from sqlalchemy.orm.session import Session

import backend.src.db.record_types as record_types
from ..db.record_repo import RecordRepository
from ..service.service_core import ServiceErrorWrapper, ServiceErrorInvoker, SError

# Constant for number of results per page during collation
RESULTS_NUM = 100

class RecordService(ServiceErrorWrapper, ServiceErrorInvoker):
    def __init__(self, session: Session, record_type: int | None):
        """A `RecordRepository` is instantiated using the provided `record_type`. Uses
        `get_record_repository` or `get_all_repositories` (if `record_type` is `None`),
        which are factory functions in `db.record_types` designed for `RecordRepository`
        initialization. Repositories are always stored in a list; use
        `get_first_repository` to access the repository passed in through the
        constructor. The service instance is initialized with a SQLAlchemy session to be
        shared across all repository instances.

        Args:
            session (Session): The SQLAlchemy session to be used for database
                transactions in the service's repositories.
            record_type (int | None): An integer corresponding to a record type, or None
                if repositories for all record types should be initialized. The integer
                values corresponding to each record type are defined in
                `db.record_types`.
        """
        self.record_repo = (
            [record_types.get_record_repository(session, record_type)] 
            if record_type is not None else 
            record_types.get_all_repositories(session)
        )
        self.session = session
        
    
    def _get_first_repository(self) -> RecordRepository:
        try:
            return self.record_repo[0]
        except IndexError as e:
            self._raise(SError.INTERNAL, "Could not access record repository!", False, e)


    def get_train_record(self, record_id: int) -> dict[str, Any]:
        """Queries the repository created in the constructor to return the signal/train
        record with the provided ID. The columns queried vary for each record type.

        Args:
            record_id (int): A value corresponding to a record's primary key.

        Returns:
            dict[str, Any]: A dictionary with keys associated to predefined columns and
                their values. The columns returned vary for each record type, for more
                information on the columns returned for each record type, check
                `docs/service.md`.
        """
        return self._get_first_repository().get_train_history(record_id)
        
    def create_train_record(self, args: dict) -> int:
        """Creates a new record in the database.

        After a record is created, the following logic occurs:
        - Attempt to automatically update a new record's symbol ID and engine number
        from the previous most recent record: `attempt_auto_fill`.
        - Update the recency status of the previous record so that the newly created
        record is the most recent: `add_new_pin`.
        - Check to see if a notification needs to be sent: `check_recent_notification`.
        - Send a notification to subscribed users using a notification service (future
        implementation).

        Creates a record using the repository created during initialization.

        Args:
            args (dict): A dictionary containing the values of the new record, where the
                keys correspond to the database columns in a record's table. See the
                additional documentation for details about the required values:
                `create_train_record` in `db.record_repo.RecordRepository`.

        Returns:
            int: ID of the newly created record.
        """
        # Get a single repository instantiated repository
        repository = self._get_first_repository()
        
        # Get the current time in EST that a record was created
        dt = self.get_current_time_est()
            
        # Don't need to check num results, creation errors are checked in repo
        record_id, recovery_request = repository.create_train_record(args, dt)
        self.attempt_auto_fill(args["unit_addr"])
        self.add_new_pin(args["unit_addr"])
        
        # Checks if a notification has been sent for a train with the same unit address at the same station recently
        has_notification = self.check_recent_notification(args["unit_addr"], args["station_id"])
        
        if not has_notification and not recovery_request:
            # TODO: Send notification
            pass
        
        return record_id

        
    def check_recent_notification(self, unit_addr: str, station_id: int) -> bool:
        """Checks if any train records with the specified unit address have been detected
        at a station within the last 10 minutes. If records exist, then this method
        indicates that a notification should be sent.

        Checks for records using the repository created during initialization.

        Args:
            unit_addr (str): The unit address corresponding to a record.
            station_id (int): The station ID a signal was detected at.

        Returns:
            bool: True if a notification should be sent out for a new record; otherwise,
                false.
        """
        results = self._get_first_repository().get_recent_trains(unit_addr, station_id)
        return results is not None and len(results) > 0
        
        
    def add_new_pin(self, unit_addr: str):
        """Updates the most recent record with the provided unit address using the
        repository created during initialization.

        Args:
            unit_addr (str): The unit address shared by multiple records  to be updated.

        Returns:
            None
        """
        repo = self._get_first_repository()
        
        # Get most recent record (the one just created)
        resp_id = repo.get_unit_record_ids(unit_addr, True)
        
        # Make the newly created record the only record where most_recent is True
        repo.add_new_pin(resp_id, unit_addr)
        
        
    def attempt_auto_fill(self, unit_addr: str):
        """Updates a record with the symbol id and engine num of the previous most recent
        record with the same unit address.

        Updates the record table using the repository created during initialization.

        Args:
            unit_addr (str): The unit address of a record to update.

        Returns:
            None
        """
        repo = self._get_first_repository()
        
        # Try to get the most recent symbol and engine values from records with the same unit address
        symb = repo.get_record_column_by_unit_addr(unit_addr, "symbol_id", most_recent=True)
        print(symb)
        symb = symb[-1] if len(symb) > 0 else None
            
        engi = repo.get_record_column_by_unit_addr(unit_addr, "engine_num", most_recent=True)
        engi = engi[-1] if len(engi) > 0 else None
        
        record_id = repo.get_unit_record_ids(unit_addr, True)
        
        # Update the record with the retrieved symbol and engine values if they exist
        repo.update_signal_values(record_id, symb, engi)
        
    
    # Signal Update
    def signal_update(self, record_id: int, symbol_id: int, engine_num: int) -> int | None:
        """Updates the symbol ID and engine number of a record using the repository created
        during initialization.

        Args:
            record_id (int): The ID of the record to update.
            symbol_id (int): The ID of a symbol to add to a record
            engine_num (int): The engine number to add to a record.

        Returns:
            int | None: _description_
        """
        result = self._get_first_repository().update_signal_values(record_id, symbol_id, engine_num)
        return result["id"] if result else None


    # Data Collation
    def get_collated_records(self, page: int, verified: Optional[bool] = None) -> dict[str, list | int]:
        """Retrieves a paginated collation of train records grouped by unit address and
        station.

        The number of records returned is defined by `NUM_RESULTS`, and the total number
        of pages is calculated based on the total number of results. Can return records
        that are verified, unverified, or both depending on the value of the `verified`
        parameter.

        Args:
            page (int): The page number of records to retrieve, 1-indexed.
            verified (Optional[bool], optional): If True or False, filters records by
                their `verified` status. If None, no filter is applied. Defaults to
                None.

        Returns:
            dict[str, list | int]: Returns a dictionary with two keys: - `results`: A
                list of records, where each record is a dictionary with keys
                corresponding to database columns. The columns returned vary for each
                record type, for more information on the columns returned for each
                record type, check `docs/api.md`. - `totalPages`: The total number of
                pages available based on the number of results and `NUM_RESULTS`.
        """
        results, pages = self._get_first_repository().get_record_collation(page, RESULTS_NUM, verified)
        return {"results": results, "totalPages": pages}


    def verify_record(self, record_id: int, symbol_id: int, locomotive_num: str | None) -> None:
        """Verifies a record by updating its symbol ID, locomotive number, and setting its
        `verified` flag to true.

        Args:
            record_id (int): The ID of the record to update.
            symbol_id (int): The ID of a symbol to add to a record.
            locomotive_num (str | None): The locomotive number to add to a record.

        Returns:
            None
        """
        self._get_first_repository().verify_record(record_id, symbol_id, locomotive_num)
        
        
    # Time frame pull
    def time_frame_pull(
        self, time_range: str, station_id: int, station_name: str, recent: Optional[bool] = None
    ) -> list[dict[str, Any]]:
        """Pulls all records that have been recorded at a station within a provided
        timerange from the current time.

        The resulting records will be sorted in descending order by the date they were
        received. This method queries record repositories for each record type, and will
        query a `StationRepository` if the station ID is not provided.

        Args:
            time_range (str): A string in the format "HH:MM:SS" representing the time
                range to pull records from relative to the current time.
            recent (bool): If True or False, only returns records based on their
                `most_recent` flag; otherwise, returns all records within the time
                frame.
            station_id (int): The ID of the station to pull records from. If `None` is
                provided, `station_name` must be provided.
            station_name (str): The name of the station to pull records from. If `None`
                is provided, `station_id` must be provided.

        Returns:
            list[dict[str, Any]]: A list of dictionaries, each representing a record
                within the specified time frame.
        """
        # This is the only method that needs to access a StationService instance.
        # Used to get the station ID if only the station name is provided.
        from .station_service import StationService
        station_service = StationService(self.session)

        # The time range is provided as a string in the format "HH:MM:SS"
        # Construct a timedelta object to calculate the time range relative to the current time
        time_increments = time_range.split(":")
        delta = datetime.timedelta(
            hours=int(time_increments[0]),
            minutes=int(time_increments[1]),
            seconds=int(time_increments[2]),
        )
        timeframe = self.get_current_time_est() - delta
        
        # If the station ID is not provided, attempt to get the station ID from its station name.
        if station_id is None:
            if station_name is not None:
                retrieved_id = station_service.get_station_id(station_name)
            else:
                self._raise(SError.INVALID_ARG, "Did not provide station name or ID!", True)
                
        # Otherwise, ensure that the station ID is a positive integer.
        else:
            if station_id < 1:
                self._raise(SError.INVALID_ARG, f"Station ID must be a positive integer, provided: {station_id}", True)
            retrieved_id = station_id

        # Query each repository for records at a station within the time frame
        return self.get_records_from_station(retrieved_id, recent, timeframe)
    
    
    def get_records_from_station(
        self, 
        station_id: int, 
        recent: Optional[bool] = None, 
        timeframe: datetime = None,
        all_cols: bool = False,
        separate_results: bool = False
    ) -> list[dict[str, Any]]:
        """Pulls all records that have been recorded at a station.

        The resulting records will be sorted in descending order by the date they were
        received. This method queries record repositories for each record type, and will
        query a `StationService` if the station ID is not provided.

        Args:
            station_id (int): The ID of the station to pull records from.
            recent (bool): If True or False, only returns records based on their
                `most_recent` flag; otherwise, returns all records within the time
                frame.
            all_cols (bool): If True, returns all columns for each record; otherwise, 
                returns only the specified columns (defined in db.record_repo.get_records_at_station).
        """
        # Should never occur, but to be safe..
        if len(self.record_repo) < 1:
            self._raise(SError.INTERNAL, "Could not find valid record access!", False)

        # Query each repository for records at a station within the time frame
        results = {}
        for repo in self.record_repo:
            results[repo.record_identifier] = repo.get_records_at_station(station_id, timeframe, recent, all_cols)
    
        # If results should be combined, merge all results into a single list and sort by date received
        if not separate_results:
            # Combine all results into a single list
            combined_results = []
            for repo_results in results.values():
                combined_results.extend(repo_results)
            
            # Sort the results in descending order by the date they were received
            combined_results.sort(key=lambda x: x["date_rec"], reverse=True)
            
            # Convert `date_rec` to a string for JSON serialization
            for row in combined_results:
                row["date_rec"] = str(row["date_rec"])
        
            return combined_results
        
        # Otherwise, return the results as a dictionary with separate lists for each record type
        for repo_results in results.values():
            # Convert `date_rec` to a string for JSON serialization
            for row in repo_results:
                row["date_rec"] = str(row["date_rec"])
                
        return results

    
    def get_current_time_est(self) -> datetime:
        """Returns a datetime object of the current time and date in EST.

        Returns:
            datetime: The datetime in EST.
        """
        est = zoneinfo.ZoneInfo("America/New_York")
        return datetime.datetime.now(tz=est).replace(tzinfo=None)
    