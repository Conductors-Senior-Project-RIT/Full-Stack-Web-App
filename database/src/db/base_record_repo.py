from abc import ABC, abstractmethod
from psycopg import Error, OperationalError, sql
from sqlalchemy import text
from sqlalchemy.orm.scoping import scoped_session
from trackSense_db_commands import run_get_cmd, run_exec_cmd
from database_core import *
from typing import Any

class RecordRepository(BaseRepository):
    def __init__(self, session: scoped_session, table_name: str, record_name: str, record_identifier: str):
        self._table_name = table_name
        self._record_name = record_name
        self._record_identifier = record_identifier
        super().__init__(session)
        
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

    
    def get_unit_record_ids(self, unit_addr: str, most_recent=False) -> int:
        try:
            query = text(
                f"""
                SELECT id FROM {self._table_name}
                WHERE unit_addr = :unit_addr
                """
            )
            
            args = {"unit_addr": unit_addr}
            resp_id = self.session.execute(query, args).scalars()
            
            if len(resp_id) < 1:
                raise RepositoryNotFoundError(unit_addr)
                
            return resp_id[-1] if most_recent else resp_id
        
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Could not get unit record IDs: {e}")
        except (TypeError, IndexError) as e:
            raise RepositoryParsingError(f"Could not parse unit record IDs: {e}")
        

    
    def get_recent_trains(self, unit_addr: str, station_id: int) -> list:
        try:
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
        
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Could not get recent trains: {e}")    


    
    def add_new_pin(self, record_id: int, unit_addr: int) -> int:
        try:
            args = {"id": record_id, "unit_addr": unit_addr}
            
            query = text(
                f"""
                UPDATE {self._table_name}
                SET most_recent = false
                WHERE id != :id and unit_addr = :unit_addr and most_recent = true
                RETURNING id
                """
            )
            
            results = self.session.execute(query, args).scalar()
            if len(results) < 1:
                raise RepositoryInternalError(f"Could not add new pin, 0 rows were updated!")
            return results
        
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Could not add new pin: {e}")


    
    def check_for_record_field(self, unit_addr: str, field_type: str):
        if field_type != "symbol_id" or field_type != "engine_num":
            raise RepositoryNotFoundError(field_type)
        
        # sql = """
        # SELECT %(field_type)s FROM {record_table} 
        # WHERE unit_addr = %(unit_addr)s and most_recent = True
        # """
        try:
            query = text(
                f"""
                SELECT {field_type} FROM {self._table_name} 
                WHERE unit_addr = :unit_addr and most_recent = True
                """
            )
            params = {"unit_addr": unit_addr}
            
            return self.session.execute(query, params).scalar()
        
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Could not check a record field: {e}")    
        except IndexError as e:
            raise RepositoryParsingError(f"Could not parse record field results: {e}")
        

    
    def update_record_field(self, record_id: int, field_value: Any, field_type: str):
        if field_type != "symbol_id" or field_type != "engine_num":
            raise RepositoryNotFoundError(field_type)
        
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
                raise RepositoryInternalError(f"Could not update {field_type}, 0 rows updated!")
            return [row._asdict() for row in results]
        
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Could not update {field_type}: {e}")


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
        
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Could not fetch records for a specific station {station_id}: {e}")
        except ValueError as e:
            raise RepositoryParsingError(f"Could not parse query: {e}")
        
    
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
                raise RepositoryNotFoundError(record_id)
            return [row._asdict() for row in results]
            
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Could not verify {self._record_name} {record_id}: {str(e)}")
        
        
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
                raise RepositoryNotFoundError(station_id)
            
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
            
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Could not retrieve {self._record_name}s in timeframe: {e}")
        except (IndexError, ValueError, TypeError) as e:
            raise RepositoryParsingError(f"Could not parse record results in timeframe: {e}")