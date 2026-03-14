from abc import ABC, abstractmethod
from typing import Any
from sqlalchemy import text
from sqlalchemy.orm.scoping import scoped_session

from .database_core import BaseRepository, RepositoryNotFoundError, RepositoryInternalError, \
    RepositoryInvalidArgumentError, repository_error_handler, repository_error_translator


class RecordRepository(ABC, BaseRepository):
    def __init__(self, session: scoped_session, table_name: str, record_name: str, record_identifier: str):
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
        
        query = text(f"SELECT * FROM {self._table_name} WHERE id = :id")
        args = {"id": _id}
        
        result = self.session.execute(query, args).one_or_none()
        
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
    def get_unit_record_ids(self, unit_addr: str, most_recent=False) -> int:
        query = text(
            f"""
            SELECT id FROM {self._table_name}
            WHERE unit_addr = :unit_addr
            """
        )
        
        args = {"unit_addr": unit_addr}
        resp_id = self.session.execute(query, args).scalars().all()
        
        if len(resp_id) < 1:
            raise RepositoryNotFoundError(
                caller_name=self.__class__.__name__,
                message=f"Could not get record ID where the unit address = {unit_addr}",
                show_error=False
            )
            
        return resp_id[-1] if most_recent else resp_id
    
    
    @repository_error_handler()
    def get_recent_trains(self, unit_addr: str, station_id: int) -> list[dict]:
        query = text(
            f"""
            SELECT * FROM {self._table_name}
            WHERE unit_addr = :unit_addr AND station_recorded = :station_id AND date_rec >= NOW() - INTERVAL '10 minutes'
            """
        )
        
        args = {
            "unit_addr": unit_addr, 
            "station_id": station_id
        }
        
        results = self.session.execute(query, args).all()
        return [row._asdict() for row in results]

    
    @repository_error_handler()
    def add_new_pin(self, record_id: int, unit_addr: int) -> list[int]:
        args = {"id": record_id, "unit_addr": unit_addr}
        
        query = text(
            f"""
            UPDATE {self._table_name}
            SET most_recent = false
            WHERE id != :id and unit_addr = :unit_addr and most_recent = true
            RETURNING id
            """
        )
        
        return self.session.execute(query, args).scalars().all()



    @repository_error_handler()
    def check_for_record_field(self, unit_addr: str, field_type: str):
        if field_type != "symbol_id" or field_type != "engine_num":
            raise RepositoryInvalidArgumentError(
                caller_name=self.__class__.__name__,
                message=f"{field_type} is not supported!",
                show_error=False
            )
        
        # sql = """
        # SELECT %(field_type)s FROM {record_table} 
        # WHERE unit_addr = %(unit_addr)s and most_recent = True
        # """
        query = text(
            f"""
            SELECT {field_type} FROM {self._table_name} 
            WHERE unit_addr = :unit_addr and most_recent = True
            """
        )
        params = {"unit_addr": unit_addr}
        
        return self.session.execute(query, params).scalar()
        

    
    def update_record_field(self, record_id: int, field_value: Any, field_type: str):
        if field_type != "symbol_id" or field_type != "engine_num":
            raise RepositoryInvalidArgumentError(
                caller_name=self.__class__.__name__,
                message=f"{field_type} is not supported!",
                show_error=False
            )
        
        try:
            args = {"id": record_id, "field_val": field_value}
            query = text(
                f"""
                UPDATE {self._table_name} 
                SET {field_type} = :field_val 
                WHERE id = :id
                RETURNING id, {field_type}
                """
            )

            results = self.session.execute(query, args).all()
            if results < 1:
                raise RepositoryInternalError(
                    caller_name=self.__class__.__name__,
                    message=f"Could not update {field_type}, 0 rows updated!",
                    show_error=False
                )
                
            return [row._asdict() for row in results]
        
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not update {field_type}: {e}"
            )


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
            return [row._asdict() for row in results]
        
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
            return [row._asdict() for row in results]
            
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
            
            return [
                {
                    "id": tup[0],
                    "unit_addr": tup[1],
                    "date_rec": str(tup[2].time())[0:5],
                    "station_name": tup[3],
                    "symbol_id": tup[4],
                    "engine_num": tup[5],
                    "locomotive_num": tup[6],
                    "Data_type": self._record_identifier.upper()
                } for tup in results
            ]
            
        except Exception as e:
            raise repository_error_translator(
                e, self.__class__.__name__, None,
                f"Could not retrieve {self._record_name}s in timeframe: {e}"
            )
