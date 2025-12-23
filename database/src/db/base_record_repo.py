from abc import ABC
from psycopg import Error, sql
from trackSense_db_commands import run_get_cmd, run_exec_cmd
import database.src.db.station_db as station_db
from typing import Any


class RecordRepository(ABC):
    def __init__(self, table_name: str):
        self._table_name = table_name

    def get_newest_record_id(self, unit_addr: str) -> int:
        query = sql.SQL(
            """
            SELECT id FROM {table_name}
            WHERE unit_addr = %(unit_addr)s
            """
        ).format(table_name=sql.Identifier(self._table_name))
        
        args = {"unit_addr": unit_addr}
        resp_id = run_get_cmd(query, args)
        return resp_id[len(resp_id) - 1][0]

    def check_recent_trains(self, unit_addr: str, station_id: int) -> bool:
        query = sql.SQL(
            """
            SELECT * FROM {table_name}
            WHERE unit_addr = %(unit_address)s AND station_recorded = %(station_id)s AND date_rec >= NOW() - INTERVAL '10 minutes'
            """
        ).format(table_name=sql.Identifier(self._table_name))
        
        args={"unit_address": unit_addr, "station_id": station_id}
        
        resp = run_get_cmd(query, args)
        if resp:  # arbitrary number that will make this work
            return True
        
        return False

    def add_new_pin(self, record_id: int, unit_addr: int, ) -> bool:
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
        run_exec_cmd(query, args)

    def check_for_record_field(self, unit_addr: str, field_type: str):
        if field_type != "symbol_id" or field_type != "engine_num":
            print("Incorrect database field!")
            return None
        
        # sql = """
        # SELECT %(field_type)s FROM {record_table} 
        # WHERE unit_addr = %(unit_addr)s and most_recent = True
        # """
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
        if len(resp) == 1:
            return resp[0][0]
        
        return None


    def update_record_field(self, record_id: int, field_value, field_type: str):
        if field_type != "symbol_id" or field_type != "engine_num":
            print("Incorrect database field!")
            return False
        
        try:
            args = {"id": record_id, "field_val": field_value}
            query = sql.SQL(
                "UPDATE {record_table} SET {field_type} = %(field_val)s WHERE id = %(id)s").format(
                record_table=sql.Identifier(self._table_name),
                field_type=sql.Identifier(field_type)
                )
            resp = run_exec_cmd(query, args)
            print(resp)
            return True
        except Exception as e:
            print(f"An error occurred while updating an EOT record's engine number: {e}")
            return False

    def get_records_for_station(self, station_id: int) -> list[tuple[Any, ...]] | None:
        """
        todo: remove methods from eot_db.py and hot_db.py that can be turned into generic handlers here.
        """
        try:

            query = sql.SQL(
                "SELECT * FROM {record_table} WHERE station_recorded = {station_id}").format(
                record_table=sql.Identifier(self._table_name),
                station_id=sql.Literal(station_id)
            )
            resp = run_get_cmd(query)
            return resp
        except Exception as e:
            print(f"An error occurred while fetching records for a specific station id{e}")
            return None