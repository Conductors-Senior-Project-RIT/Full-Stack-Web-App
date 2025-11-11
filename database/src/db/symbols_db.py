"""
Symbols database layer 

This module handles all database CRUD operations for Symbol records
"""

from typing import Optional, Any
from trackSense_db_commands import run_get_cmd, run_exec_cmd


def get_symbol_name(id: int) -> str:
    """
    TODO: integrate this function to replace sql queries in train_history.py's def get_eot() 
    Returns symbol name for train given an id
    "id": The id of a train record to retrieve.
    """

    if not isinstance(id, int):
        raise ValueError(f"id ({id}) is not an integer")
    
    sql = "SELECT symb_name FROM Symbols WHERE id = %(symid)s"
    named_args = {"symid": id}

    return run_get_cmd(sql, named_args)
