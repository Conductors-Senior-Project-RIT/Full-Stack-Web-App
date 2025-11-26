from argparse import Namespace
from math import ceil
from flask import Response, jsonify
from api_strat import Record_API_Strategy
import database.src.db.eot_db as eot_db
import database.src.db.generic_record_db as generic_db
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
            
            has_notification = self.check_recent_notification(args["unit_addr"], args["station_id"])
            
            if not has_notification and not recovery_request:
                # Send notification for EOT
                pass
                
        return 200
    
    
    
    