from argparse import Namespace
from math import ceil
from flask import Response, jsonify
from api_strat import Record_API_Strategy
import database.src.db.eot_db as eot_db
from database.src.db.trackSense_db_commands import run_exec_cmd, run_get_cmd

class EOT_API_Strategy(Record_API_Strategy):
    def get_train_history(self, id, page, results_num) -> Response:
        # TODO: Move  to db
        sql = """SELECT EOTRecords.id, date_rec, stat.station_name, symbol_id, unit_addr, brake_pressure, motion, marker_light, turbine, battery_cond, battery_charge, arm_status, signal_strength, verified FROM EOTRecords
                INNER JOIN Stations as stat on station_recorded = stat.id"""
        
        sql += "WHERE EOTRecords.id = %(id)s ORDER BY EOTRecords.id Desc" if id == 1 else "ORDER BY date_rec DESC"
        sql += "LIMIT %(results_num)s OFFSET %(offset)s * %(results_num)s"
        
        sql_args = {"results_num": results_num, "offset": page - 1}
        if id == 1:
            sql_args["id"] = id
            resp = run_get_cmd(sql, sql_args) # BUG: move this LOC above if block so it's accessible by else block as well
            return jsonify(
                [
                    {
                        "id": tup[0],
                        "date_rec": tup[1],
                        "station_name": tup[2],
                        "symbol_name": run_get_cmd(
                            "SELECT symb_name FROM Symbols WHERE id = %(symid)s",
                            {"symid": tup[3]},
                        ),
                        "unit_addr": tup[4],
                        "brake_pressure": tup[5],
                        "motion": tup[6],
                        "marker_light": tup[7],
                        "turbine": tup[8],
                        "battery_cond": tup[9],
                        "battery_charge": tup[10],
                        "arm_status": tup[11],
                        "signal_strength": tup[12],
                        "verified": tup[13],
                    }
                    for tup in resp
                ]
            ), 200
              
        # BUG: in the else block it is trying to reference "resp" but it's out of scope...
        else:
            count_sql = """SELECT COUNT(*) FROM EOTRecords"""
            count = run_get_cmd(count_sql)

            return jsonify(
                {
                    "results": [
                        {
                            "id": tup[0],
                            "date_rec": tup[1],
                            "station_name": tup[2],
                            "symbol_name": tup[3],
                            "unit_addr": tup[4],
                            "brake_pressure": tup[5],
                            "motion": tup[6],
                            "marker_light": tup[7],
                            "turbine": tup[8],
                            "battery_cond": tup[9],
                            "battery_charge": tup[10],
                            "arm_status": tup[11],
                            "signal_strength": tup[12],
                            "verified": tup[13],
                        }
                        for tup in resp
                    ],
                    "totalPages": ceil(count[0][0] / results_num),
                }
            ), 200
            
    def post_train_history(self, args: Namespace, datetime_str: str):
        # TODO: Implement better parsing and response handling
        resp, recovery_request = eot_db.create_eot_record(dict(args), datetime_str)
        # Do error handling etc.
        if not resp:
            self.add_new_pin(args["unit_addr"])
            has_notification = eot_db.check_eot_notification(args["unit_addr"], args["station_id"])
            
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
        
        if symb:
            id = eot_db.get_newest_eot_id(unit_addr)
            resp = eot_db.update_eot_field(id, symb, "symbol_id")
        
        if engi:
            id = eot_db.get_newest_eot_id(unit_addr)
            resp = eot_db.update_eot_field(id, engi, "engine_num")
        else:
            print("No engine number to update!")
    
    
    