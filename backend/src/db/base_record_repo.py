from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Type
from sqlalchemy import func, select, text, update
from sqlalchemy.orm.scoping import scoped_session

from ...database import Base
from .database_core import BaseRepository, RepositoryNotFoundError, RepositoryInternalError, \
    RepositoryInvalidArgumentError, repository_error_handler, repository_error_translator


class RecordRepository(ABC, BaseRepository):
    def __init__(
        self, 
        session: scoped_session, 
        model: Type[Base], 
        table_name: str, 
        record_name: str, 
        record_identifier: str
    ):
        self._model = model 
        self._table_name = table_name
        self._record_name = record_name
        self._record_identifier = record_identifier
        super().__init__(session)
        
    def get_record_name(self) -> str:
        return self._record_name
        
    def get_record_identifier(self) -> str:
        return self._record_identifier
    
    def get_train_record(self, _id: int) -> dict[str, Any]:
        if not isinstance(_id, int):
            raise RepositoryInvalidArgumentError(
                self.__class__.__name__,
                None,
                f"Invalid type provided: {type(_id)}",
                False
            )
            
        result = self.session.get(self._model, _id)
        
        # query = text(f"SELECT * FROM {self._table_name} WHERE id = :id")
        # args = {"id": _id}
        
        # result = self.session.execute(query, args).one_or_none()
        
        if result is None:
            raise RepositoryNotFoundError(
                self.__class__.__name__,
                None,
                f"Could not find record with an ID: {_id}",
                True
            ) 
        
        return result._asdict()
        
    @abstractmethod
    def get_train_history(self, id: int, page: int, num_results: int) -> list[dict[str,Any]]:
        pass
    
    @abstractmethod
    def create_train_record(self, args: dict[str, Any], datetime_string: str) -> tuple[int, bool]:
        pass

    @repository_error_handler()
    def get_unit_record_ids(self, unit_addr: str, recent=False) -> int | list[int]:
        # query = text(
        #     f"""
        #     SELECT id FROM {self._table_name}
        #     WHERE unit_addr = :unit_addr
        #     """
        # )
        
        # args = {"unit_addr": unit_addr}
        # resp_id = self.session.execute(query, args).scalars().all()
        
        stmt = (
            select(self._model.id)
            .where(self._model.unit_addr == unit_addr)
            .order_by(self._model.id.asc())
        )
        result = self.session.execute(stmt).scalars().all()
        
        if not result:
            raise RepositoryNotFoundError(
                caller_name=self.__class__.__name__,
                message=f"Could not get record ID where the unit address = {unit_addr}",
                show_error=False
            )
            
        return result[-1] if recent else result
    
    
    @repository_error_handler()
    def get_recent_trains(self, unit_addr: str, station_id: int) -> list[dict]:
        # query = text(
        #     f"""
        #     SELECT * FROM {self._table_name}
        #     WHERE unit_addr = :unit_addr AND station_recorded = :station_id AND date_rec >= NOW() - INTERVAL '10 minutes'
        #     """
        # )
        
        # args = {
        #     "unit_addr": unit_addr, 
        #     "station_id": station_id
        # }
        # results = self.session.execute(query, args).all()
        
        stmt = (
            select(self._model)
            .where(
                self._model.unit_addr == unit_addr,
                self._model.station_recorded == station_id,
                self._model.date_rec >= func.now() - text("INTERVAL '10 minutes'")
            )
        )
        
        results = self.session.execute(stmt).all()
        return self.rows_to_dicts(results)

    
    @repository_error_handler()
    def add_new_pin(self, record_id: int, unit_addr: str) -> list[int]:
        # args = {"id": record_id, "unit_addr": unit_addr}
        
        # query = text(
        #     f"""
        #     UPDATE {self._table_name}
        #     SET most_recent = false
        #     WHERE id != :id and unit_addr = :unit_addr and most_recent = true
        #     RETURNING id
        #     """
        # )
        
        # return self.session.execute(query, args).scalars().all()
        stmt = (
            update(self._model)
            .where(
                self._model.id != record_id,
                self._model.unit_addr == unit_addr,
                self._model.most_recent.is_(True)
            )
            .values(most_recent=False)
            .returning(self._model.id)
        )
        
        result = self.session.execute(stmt).scalars().all()
        return result
        
    

    @repository_error_handler()
    def get_record_column_by_unit_addr(
        self, 
        unit_addr: str, 
        field_type: str, 
        result_position: str,
        most_recent: bool | None = None, 
    ) -> Any | list[Any]:    
         
        if not hasattr(self._model, field_type):
            raise RepositoryInvalidArgumentError(
                self.__class__.__name__,
                f"Column '{field_type}' not found in {self._model.__name__}!",
                True
            )
        
        stmt = (
            select(getattr(self._model, field_type))
            .where(self._model.unit_addr == unit_addr)
            .order_by(self._model.id.asc())
        )
        
        if most_recent is not None:
            stmt = stmt.where(self._model.most_recent.is_(most_recent))
        
        result = self.session.execute(stmt).scalars().all()
        
        if not result or result_position == "all":
            return result
        
        match result_position:
            case "first":
                return result[0]
            case "last":
                return result[-1]
        
        raise RepositoryInvalidArgumentError(
            self.__class__.__name__,
            f"Invalid result position: {result_position}!",
            True
        )
         
    
    def update_record_column_by_id(self, record_id: int, column_value: int, column_name: str) -> tuple[int, Any]:
        # args = {"id": record_id, "field_val": field_value}
        # query = text(
        #     f"""
        #     UPDATE {self._table_name} 
        #     SET {field_type} = :field_val 
        #     WHERE id = :id
        #     RETURNING id, {field_type}
        #     """
        # )
        
        record = self.session.get(self._model, record_id)
        if not record:
            raise RepositoryNotFoundError(
                self.__class__.__name__,
                f"Could find record to update with an ID = {record_id}, 0 rows updated!",
                True
            )
            
        if not hasattr(self._model, column_name):
            raise RepositoryInvalidArgumentError(
                self.__class__.__name__,
                f"Column '{column_name}' not found in {self._model.__name__}!",
                True
            )
        
        # Update the value
        setattr(record, column_name, column_value)
        
        return record.id, getattr(record, column_name)


    # Station Handler
    def get_station_records(self, station_id: int, recent=False) -> list[tuple[Any, ...]]:
        try:
            if recent:
                return self.get_recent_station_records(station_id)
            
            args = {"station_id": station_id}
            query = text(
                f"SELECT * FROM {self._table_name} WHERE station_recorded = :station_id"
            )
            
            results = self.session.execute(query, args).all()
            return self.rows_to_dicts(results)
        
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not fetch records for a specific station {station_id}: {e}"
            )
        
    
    @abstractmethod
    def get_recent_station_records(self, station_id: int) -> list[tuple[Any, ...]]:
        pass
        
        
    @abstractmethod
    def parse_station_records(self, station_records: list[tuple[Any, ...]]) -> list[dict[str, Any]]:
        pass
    
    @abstractmethod
    def get_record_collation(self, page: int) -> list[dict[str, str]]:
        pass
    
    
    # Record Verification
    @abstractmethod
    def get_records_by_verification(self, page: int, verified: bool) -> list[dict[str, str]]:
        pass
    
    
    def verify_record(self, record_id: int, symbol_id: int, engine_id: int):
        try:
            args = {
                "id": record_id,
                "symbol": symbol_id,
                "engine_num": engine_id,
            }
            
            query = text(
                f"""
                UPDATE {self._table_name}
                SET symbol_id = :symbol, 
                locomotive_num = :engine_num,
                verified = true
                WHERE id = :id
                RETURNING id, symbol_id, locomotive_num
                """
            )

            results = self.session.execute(query, args).all()
            if results < 1:
                raise RepositoryNotFoundError(
                    caller_name=self.__class__.__name__, 
                    message=f"Could not find record with id: {record_id}!",
                    show_error=False
                )
            return self.rows_to_dicts(results)
            
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not verify {self._record_name} {record_id}: {e}"
            )
        
        
    # Time frame
    def get_records_in_timeframe(self, station_id: int, datetime_str: str, recent: bool) -> list[dict[str, Any]]:
        try:
            query_str = f"""
                SELECT {self._table_name}.id, unit_addr, date_rec, stat.station_name, sym.symb_name, engine_num, locomotive_num FROM {self._table_name}
                INNER JOIN Stations as stat on station_recorded = stat.id
                INNER JOIN Symbols as sym on symbol_id = sym.id
                WHERE date_rec >= :date_stamp 
                """
            
            args = {"date_stamp": datetime_str}
            
            if station_id != -1:  
                query_str += " AND stat.id = :station_id" if station_id != -1 else ""
                args["station_id"] = station_id
            
            if recent:
                query_str += " AND most_recent = TRUE"
                
            query = text(query_str)
            results = self.session.execute(query, args).all()
            if len(results) < 1:
                raise RepositoryNotFoundError(
                    caller_name=self.__class__.__name__, 
                    message=f"Could not find record with corresponding station: {station_id}!",
                    show_error=False
                )
            
            results = self.rows_to_dicts(results)
            # Add data type to result
            for result in results:
                result["Data_type"] = self._record_identifier.upper()
            
            return results
            
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not retrieve {self._record_name}s in timeframe: {e}"
            )
