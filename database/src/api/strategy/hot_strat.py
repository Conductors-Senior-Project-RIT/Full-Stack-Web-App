from flask import Response, jsonify
from api_strat import Record_API_Strategy
from database.src.db.trackSense_db_commands import run_get_cmd

class HOT_API_Strategy(Record_API_Strategy):
    def get_train_history(self, id: int, page: int, results_num: int) -> Response:
        sql = """
            SELECT HOTRecords.id, date_rec, stat.station_name, symbol_id, unit_addr, command, checkbits, parity, verified FROM HOTRecords
            INNER JOIN Stations as stat on station_recorded = stat.id
            WHERE HOTRecords.id = %(id)s
            LIMIT %(results_num)s OFFSET %(offset)s * %(results_num)s
            """
        sql_args = {"id": id, "results_num": results_num, "offset": page - 1}
        resp = run_get_cmd(sql, sql_args)
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
                    "command": tup[5],
                    "checkbits": tup[6],
                    "parity": tup[7],
                    "verified": tup[8],
                }
                for tup in resp
            ]
        ), 200
        
    def post_train_history(self, args, datetime_str):
        return super().post_train_history(args, datetime_str)