from argparse import Namespace
from math import ceil
from flask import Response, jsonify
from api_strat import Record_API_Strategy
import database.src.db.eot_db as eot_db
from database.src.db.trackSense_db_commands import run_exec_cmd, run_get_cmd

class EOT_API_Strategy(Record_API_Strategy):
    
    ## Train History API Implementation
    
    def get_train_history(self, id, page, results_num) -> Response:
        try:
            results = eot_db.get_eot_data_by_train_id(id, page, results_num)
            if not results:
                jsonify({"error": "Error occurred when attempting to retrieve EOT records from the db!"}), 500
            jsonify(results), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        
            
    def post_train_history(self, args: Namespace, datetime_str: str):
        # TODO: Implement better parsing and response handling
        resp, recovery_request = eot_db.create_eot_record(dict(args), datetime_str)
        # Do error handling etc.
        if not resp:
            self.add_new_pin(args["unit_addr"])
            has_notification = eot_db.check_recent_eot_trains(args["unit_addr"], args["station_id"])
            
            if not has_notification and not recovery_request:
                # Send notification
                pass
                
        return 200
    
    def add_new_pin(self, unit_addr: str):
        self.attempt_auto_fill(unit_addr)
        
        resp_eot_id = eot_db.get_newest_eot_id(unit_addr)
        result = eot_db.add_new_eot_pin(unit_addr, resp_eot_id)
    
    def attempt_auto_fill(self, unit_addr):
        symb = eot_db.check_for_eot_field(unit_addr, "symbol_id")
        engi = eot_db.check_for_eot_field(unit_addr, "engine_num")
        id = eot_db.get_newest_eot_id(unit_addr)
        
        if symb:
            resp = eot_db.update_eot_field(id, symb, "symbol_id")
        
        if engi:
            resp = eot_db.update_eot_field(id, engi, "engine_num")
        else:
            print("No engine number to update!")
    
    
    