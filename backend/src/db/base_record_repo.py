from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generic, Type, TypeVar
from sqlalchemy import func, select, text, update
from sqlalchemy.orm.session import Session

from .db_core.models import EOTRecord, HOTRecord
from .db_core.repository import BaseRepository
from .db_core.exceptions import (
    RepositoryNotFoundError, RepositoryInvalidArgumentError, 
    repository_error_handler, repository_error_translator)

RecordType = TypeVar("RecordType", HOTRecord, EOTRecord)

class RecordRepository(ABC, BaseRepository[RecordType], Generic[RecordType]): 
    def __init__(
        self, 
        model: Type[RecordType],
        session: Session,  
        record_name: str = "Unknown", 
        record_identifier: str = "Unknown"
    ):
        super().__init__(model, session)
        self._record_name = record_name
        self._record_identifier = record_identifier
        
        
    def get_record_name(self) -> str:
        return self._record_name
        
    def get_record_identifier(self) -> str:
        return self._record_identifier
    
        
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
            select(self.model.id)
            .where(self.model.unit_addr == unit_addr)
            .order_by(self.model.id.asc())
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
            select(self.model)
            .where(
                self.model.unit_addr == unit_addr,
                self.model.station_recorded == station_id,
                self.model.date_rec >= func.now() - text("INTERVAL '10 minutes'")
            )
        )
        
        results = self.session.execute(stmt).all()
        return self.objs_to_dicts(results)

    
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
            update(self.model)
            .where(
                self.model.id != record_id,
                self.model.unit_addr == unit_addr,
                self.model.most_recent == True
            )
            .values(most_recent=False)
            .returning(self.model.id)
        )
        
        result = self.session.execute(stmt).scalars().all()
        self.session.flush()
        return result
        
    
    @repository_error_handler()
    def get_record_column_by_unit_addr(
        self, 
        unit_addr: str, 
        field_type: str, 
        most_recent: bool | None = None, 
    ) -> Any | list[Any]:    
         
        if not hasattr(self.model, field_type):
            raise RepositoryInvalidArgumentError(
                self.__class__.__name__,
                f"Column '{field_type}' not found in {self.model.__name__}!",
                True
            )
        
        stmt = (
            select(getattr(self.model, field_type))
            .where(self.model.unit_addr == unit_addr)
            .order_by(self.model.id.asc())
        )
        
        if most_recent is not None:
            stmt = stmt.where(self.model.most_recent == most_recent)
        
        return self.session.execute(stmt).scalars().all()

    
    @repository_error_handler()
    def update_signal_values(self, record_id: int, symbol_id: int, engine_num: int) -> dict[str, Any]:
        values = {}
        if symbol_id:
            values["symbol_id"] = symbol_id
        if engine_num:
            values["engine_num"] = engine_num
            
        return self.update_with_pk(record_id, values)  # Already flushes


    # Station Handler
    def get_station_records(self, station_id: int, recent=False) -> list[dict[str, Any]]:
        try:
            if recent:
                return self.get_recent_station_records(station_id)
            
            # args = {"station_id": station_id}
            # query = text(
            #     f"SELECT * FROM {self._table_name} WHERE station_recorded = :station_id"
            # )
            
            results = self.session.execute(
                select(self.model)
                .where(self.model.station_recorded == station_id)
            ).all()
  
            return self.objs_to_dicts(results)
        
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Error fetching records for a specific station {station_id}: {e}"
            )
        
    
    @abstractmethod
    def get_recent_station_records(self, station_id: int) -> list[tuple[Any, ...]]:
        pass
    
    
    @abstractmethod
    def get_record_collation(self, page: int, num_results: int, verified: bool | None = None) -> list[dict[str, list | str]]:
        pass
    
    
    def verify_record(self, record_id: int, symbol_id: int, locomotive_num: str) -> dict[str, Any]:
        try:
            # args = {
            #     "id": record_id,
            #     "symbol": symbol_id,
            #     "engine_num": engine_id,
            # }
            
            # query = text(
            #     f"""
            #     UPDATE {self._table_name}
            #     SET symbol_id = :symbol, 
            #     locomotive_num = :engine_num,
            #     verified = true
            #     WHERE id = :id
            #     RETURNING id, symbol_id, locomotive_num
            #     """
            # )
            
            values = {
                "symbol_id": symbol_id,
                "locomotive_num": locomotive_num,
                "verified": True
            }
            
            return self.update_with_pk(record_id, values)  # Already flushes
            
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not verify {self._record_name} {record_id}: {e}"
            )
        
        
    # Time frame
    def get_records_in_timeframe(self, station_id: int, dt: datetime, recent: bool) -> list[dict[str, Any]]:
        from .db_core.models import Symbol, Station
        
        try:
            # query_str = f"""
            #     SELECT {self._table_name}.id, unit_addr, date_rec, stat.station_name, sym.symb_name, engine_num, locomotive_num FROM {self._table_name}
            #     INNER JOIN Stations as stat on station_recorded = stat.id
            #     INNER JOIN Symbols as sym on symbol_id = sym.id
            #     WHERE date_rec >= :date_stamp 
            #     """
            
            # args = {"date_stamp": dt}
            
            stmt = (
                select(
                    self.model.id, 
                    self.model.unit_addr,
                    self.model.date_rec,
                    Station.station_name,
                    Symbol.symb_name,
                    self.model.engine_num,
                    self.model.locomotive_num
                )
                .join(Station, self.model.station_recorded == Station.id)
                .join(Symbol, self.model.symbol_id == Symbol.id)
                .where(self.model.date_rec >= dt)
            )
            
            if station_id != -1:  
                stmt = stmt.where(Station.id == station_id)
                # query_str += " AND stat.id = :station_id" if station_id != -1 else ""
                # args["station_id"] = station_id
            
            if recent:
                stmt = stmt.where(self.model.most_recent == True)
                # query_str += " AND most_recent = TRUE"
                
            #query = text(query_str)
            results = self.session.execute(stmt).all()
            # if len(results) < 1:
            #     raise RepositoryNotFoundError(
            #         caller_name=self.__class__.__name__, 
            #         message=f"Could not find record with corresponding station: {station_id}!",
            #         show_error=False
            #     )
            
            results = self.objs_to_dicts(results)
            # Add data type to result
            for result in results:
                result["Data_type"] = self._record_identifier.upper()
            
            return results
            
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not retrieve {self._record_name}s in timeframe: {e}"
            )
