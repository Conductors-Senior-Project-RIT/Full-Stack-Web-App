from abc import ABC, abstractmethod
from psycopg import Error, OperationalError, sql
from trackSense_db_commands import run_get_cmd, run_exec_cmd
from database_status import *
from typing import Any

class RecordRepository(ABC):
    def __init__(self, table_name: str, record_name: str):
        self._table_name = table_name
        self._record_name = record_name
        
    def get_record_name(self) -> str:
        return self._record_name
        
    @abstractmethod
    def get_train_history(self, id: int, page: int, num_results: int) -> list[dict[str,Any]]:
        pass
    
    @abstractmethod
    def create_train_record(self, args: dict[str, Any], datetime_string: str) -> tuple[int, bool]:
        pass

    def get_unit_record_ids(self, unit_addr: str, most_recent=False) -> int:
        try:
            query = sql.SQL(
                """
                SELECT id FROM {table_name}
                WHERE unit_addr = %(unit_addr)s
                """
            ).format(table_name=sql.Identifier(self._table_name))
            
            args = {"unit_addr": unit_addr}
            resp_id = run_get_cmd(query, args)
            
            if len(resp_id) < 1:
                raise RepositoryNotFoundError(unit_addr)
                
            return resp_id[-1][0] if most_recent else [resp_id[i][0] for i in resp_id]
        
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Could not get unit record IDs: {e}")
        except (TypeError, IndexError) as e:
            raise RepositoryParsingError(f"Could not parse unit record IDs: {e}")
        

    def get_recent_trains(self, unit_addr: str, station_id: int) -> list:
        try:
            query = sql.SQL(
                """
                SELECT * FROM {table_name}
                WHERE unit_addr = %(unit_address)s AND station_recorded = %(station_id)s AND date_rec >= NOW() - INTERVAL '10 minutes'
                """
            ).format(table_name=sql.Identifier(self._table_name))
            
            args = {
                "unit_address": unit_addr, 
                "station_id": station_id
            }
            
            return run_get_cmd(query, args)
        
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Could not get recent trains: {e}")    

    def add_new_pin(self, record_id: int, unit_addr: int) -> int:
        try:
            args = {"id": record_id, "unit_addr": unit_addr}
            query = sql.SQL(
                """
                UPDATE {table_name}
                SET most_recent = false
                WHERE id != %(id)s and unit_addr = %(unit_addr)s and most_recent = true
                """
            ).format(
                table_name=sql.Identifier(self._table_name)
            )
            results = run_exec_cmd(query, args)
            if results < 1:
                raise RepositoryInternalError(f"Could not add new pin, 0 rows were created!")
            return results
        
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Could not add new pin: {e}")


    def check_for_record_field(self, unit_addr: str, field_type: str):
        if field_type != "symbol_id" or field_type != "engine_num":
            raise ValueError("Incorrect database field!")
        
        # sql = """
        # SELECT %(field_type)s FROM {record_table} 
        # WHERE unit_addr = %(unit_addr)s and most_recent = True
        # """
        try:
            query = sql.SQL(
                    """
                    SELECT {field_type} FROM {record_table} 
                    WHERE unit_addr = %(unit_addr)s and most_recent = True
                    """).format(
                        field_type=sql.Identifier(field_type),
                        record_table=sql.Identifier(self._table_name)
                    )
            params = {"unit_addr": unit_addr}

            resp = run_get_cmd(query, params)
            return resp[0][0] if len(resp) == 1 else None
        
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Could not check a record field: {e}")    
        except IndexError as e:
            raise RepositoryParsingError(f"Could not parse record field results: {e}")
        


    def update_record_field(self, record_id: int, field_value: Any, field_type: str):
        if field_type != "symbol_id" or field_type != "engine_num":
            print("Incorrect database field!")
            return False
        
        try:
            args = {"id": record_id, "field_val": field_value}
            query = sql.SQL(
                    "UPDATE {record_table} SET {field_type} = %(field_val)s WHERE id = %(id)s"
                ).format(
                    record_table=sql.Identifier(self._table_name),
                    field_type=sql.Identifier(field_type)
                )
            resp = run_exec_cmd(query, args)
            if resp < 1:
                raise RepositoryInternalError(f"Could not update {field_type}, 0 rows updated!")
            return resp
        
        except OperationalError:
            raise RepositoryTimeoutError()
        except Error as e:
            raise RepositoryInternalError(f"Could not update {field_type}: {e}")


    # Station Handler
    def get_station_records(self, station_id: int, recent=False) -> list[tuple[Any, ...]]:
        try:
            if recent:
                return self.get_recent_station_records(station_id)
            
            query = sql.SQL(
                    "SELECT * FROM {record_table} WHERE station_recorded = {station_id}"
                ).format(
                    record_table=sql.Identifier(self._table_name),
                    station_id=sql.Literal(station_id)
                )
            resp = run_get_cmd(query)
            return resp
        
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