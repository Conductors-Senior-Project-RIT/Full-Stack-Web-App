from flask import Response, jsonify
from api_strat import Record_API_Strategy
import database.src.db.hot_db as hot_db
from database.src.db.trackSense_db_commands import run_get_cmd

class HOT_API_Strategy(Record_API_Strategy):
    def get_train_history(self, id: int, page: int, results_num: int) -> Response:
        try:
            results = hot_db.get_hot_data_by_train_id(id, page, results_num)
            if not results:
                return jsonify({"error": "Error occurred when attempting to retrieve HOT records from the db!"}), 500
            return jsonify(results), 200
        except ValueError as e:
            return jsonify({"error": str(e)})
        
    def post_train_history(self, args, datetime_str):
        # TODO: Implement better parsing and response handling
        resp, recovery_request = hot_db.create_hot_record(dict(args), datetime_str)
        # Do error handling etc.
        if not resp:
            self.add_new_pin(args["unit_addr"])
            has_notification = hot_db.check_recent_hot_trains(args["unit_addr"], args["station_id"])
            
            if not has_notification and not recovery_request:
                # Send notification
                pass
                
        return 200
    
    def add_new_pin(self, unit_addr: str):
        self.attempt_auto_fill(unit_addr)
        
        resp_eot_id = hot_db.get_newest_hot_id(unit_addr)
        result = hot_db.add_new_hot_pin(unit_addr, resp_eot_id)
        
    
    def attempt_auto_fill(self, unit_addr):
        symb = hot_db.check_for_hot_field(unit_addr, "symbol_id")
        engi = hot_db.check_for_hot_field(unit_addr, "engine_num")
        id = hot_db.get_newest_hot_id(unit_addr)
        
        if symb:
            resp = hot_db.update_hot_field(id, symb, "symbol_id")
        
        if engi:
            resp = hot_db.update_hot_field(id, symb, "engine_num")
        else:
            print("No engine number to update!")
            
        