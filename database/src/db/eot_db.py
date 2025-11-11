"""
EOT database layer 

This module handles all database CRUD operations for EOT records
"""

from trackSense_db_commands import run_get_cmd, run_exec_cmd

RESULTS_NUM = 250

def get_eot_data(id, page):
    return