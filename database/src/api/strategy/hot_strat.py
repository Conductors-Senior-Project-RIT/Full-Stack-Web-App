from flask import Response, jsonify
from api_strat import Record_API_Strategy
import database.src.db.hot_db as hot_db
import database.src.db.generic_record_db as generic_db
from database.src.db.trackSense_db_commands import run_get_cmd

class HOT_API_Strategy(Record_API_Strategy):
    def __init__(self, value):
        super().__init__(value)
    
    def get_train_history(self, id: int, page: int, results_num: int) -> Response:
        try:
            results = hot_db.get_hot_data_by_train_id(id, page, results_num)
            if not results:
                return jsonify({"error": "Error occurred when attempting to retrieve HOT records from the db!"}), 500
            return jsonify(results), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        
    def post_train_history(self, args, datetime_str):
        # TODO: Implement better parsing and response handling
        resp, recovery_request = hot_db.create_hot_record(dict(args), datetime_str)
        # Do error handling etc.
        if not resp:
            self.add_new_pin(args["unit_addr"])
            
            has_notification = self.check_recent_notification(args["unit_addr"], args["station_id"])
            
            if not has_notification and not recovery_request:
                # Send notification for HOT
                pass
                
        return 200
    
    def add_new_pin(self, unit_addr):
        return super().add_new_pin(unit_addr)
        
    
    def attempt_auto_fill(self, unit_addr):
        return super().attempt_auto_fill(unit_addr)
            
        