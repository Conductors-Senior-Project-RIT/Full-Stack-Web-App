from flask import Blueprint, request, jsonify
from flask_cors import CORS
from database.src.service.station_service import StationService
from database.src.service.service_core import *
from db.db import db

station_bp = Blueprint("station_bp", __name__)
CORS(station_bp)  # Enable CORS for the station_bp blueprint

@station_bp.route("/api/get-trains", methods=["GET"])
def get_trains():
    station = request.args.get("station")
    if not station:
        return jsonify({"message": "Station not specified"}), 400

    try:
        session = db.session
        results = StationService(session).get_trains_from_station(station)
        return jsonify(results), 200
    except ServiceTimeoutError:
        return jsonify({"error": "Request timed out!"}), 408
    except ServiceResourceNotFound as e:
        return jsonify({"error": str(e)}), 404
    except (ServiceInternalError, ServiceParsingError) as e:
        return jsonify({"error": str(e)}), 500

    # # Fetch the station ID for the specified station
    # station_id = run_get_cmd(
    #     "SELECT id FROM Stations WHERE station_name = %s", (station,)
    # )
    # if not station_id:
    #     return jsonify({"message": "Station not found"}), 404
    #
    # station_id = station_id[0][0]
    #
    # # Fetch EOTRecords for the specified station
    # eot_records = run_get_cmd(
    #     "SELECT * FROM EOTRecords WHERE station_recorded = %s", (station_id,)
    # )
    # eot_records = [
    #     {
    #         "date_rec": record[1],
    #         "unit_addr": record[4],
    #         "brake_pressure": record[5],
    #         "motion": record[6],
    #         "marker_light": record[7],
    #         "turbine": record[8],
    #         "battery_cond": record[9],
    #         "battery_charge": record[10],
    #         "arm_status": record[11],
    #         "signal_stength": record[12],
    #     }
    #     for record in eot_records
    # ]
    #
    # # Fetch HOTRecords for the specified station
    # hot_records = run_get_cmd(
    #     "SELECT * FROM HOTRecords WHERE station_recorded = %s", (station_id,)
    # )
    # hot_records = [
    #     {
    #         "id": record[0],
    #         "date_rec": record[1],
    #         "frame_sync": record[3],
    #         "unit_addr": record[4],
    #         "command": record[5],
    #         "checkbits": record[6],
    #         "parity": record[7],
    #     }
    #     for record in hot_records
    # ]
    #
    # return jsonify({"eot_records": eot_records, "hot_records": hot_records})

@station_bp.route("/api/get-pin-info", methods=["GET"])
# todo: refactor like above, just will get most recent station for type
def get_pin_info():
    station = request.args.get("station")
    if not station:
        return jsonify({"message": "Station not specified"}), 400

    session = db.session
    results = StationService(session).get_trains_from_station(station, recent=True)
    return jsonify(results), 200
    

    # Fetch the station ID for the specified station
    # station_id = run_get_cmd(
    #     "SELECT id FROM Stations WHERE station_name = %s", (station,)
    # )
    # if not station_id:
    #     return jsonify({"message": "Station not found"}), 404

    # station_id = station_id[0][0]

    # # Fetch EOTRecords for the specified station
    # eot_records = run_get_cmd(
    #     "SELECT * FROM EOTRecords WHERE station_recorded = %s and most_recent = true INNER JOIN Symbols ON EOTRecords.symbol_id = Symbols.id INNER JOIN Engine_Numbers ON EOTRecords.engine_num = Engine_Numbers.id",
    #     (station_id,),
    # )
    # eot_records = [
    #     {
    #         "date_rec": record[1],
    #         "symbol_id": record[3],
    #         "engine_num": record[4],
    #         "unit_addr": record[5],
    #         "brake_pressure": record[6],
    #         "motion": record[7],
    #         "marker_light": record[8],
    #         "turbine": record[9],
    #         "battery_cond": record[10],
    #         "battery_charge": record[11],
    #         "arm_status": record[12],
    #         "signal_stength": record[13],
    #     }
    #     for record in eot_records
    # ]

    # # eot_records.handler(station_name, most_recent=True)
    # # internally use the station_id retrieved from station_name

    # # Fetch HOTRecords for the specified station
    # hot_records = run_get_cmd(
    #     "SELECT * FROM HOTRecords WHERE station_recorded = %s and most_recent = true",
    #     (station_id,),
    # )
    # hot_records = [
    #     {
    #         "id": record[0],
    #         "date_rec": record[1],
    #         "frame_sync": record[3],
    #         "unit_addr": record[4],
    #         "command": record[5],
    #         "checkbits": record[6],
    #         "parity": record[7],
    #     }
    #     for record in hot_records
    # ]

    # return jsonify({"eot_records": eot_records, "hot_records": hot_records})
