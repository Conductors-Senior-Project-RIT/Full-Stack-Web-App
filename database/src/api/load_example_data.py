from flask_restful import Resource
from src.db.trackSense_db_commands import *
class LoadExampleData(Resource):
    def get(self):
        # Existing stations
        stations = [
            {"name": "Fairport", "pass": "password"},
            {"name": "Churchville", "pass": "password"},
            {"name": "Macedon", "pass": "password"},
            {"name": "Rotterdam", "pass": "password"},
            {"name": "Silver Springs", "pass": "password"},
            {"name": "Hornell", "pass": "password"},
        ]

        # Insert stations into the Stations table
        for station in stations:
            station_id = run_get_cmd(
                "SELECT id FROM Stations WHERE station_name = %s", (station["name"],)
            )
            if not station_id:
                run_exec_cmd(
                    """
                    INSERT INTO Stations (station_name, passwd)
                    VALUES (%s, %s)
                """,
                    (station["name"], station["pass"]),
                )
                station_id = run_get_cmd(
                    "SELECT id FROM Stations WHERE station_name = %s",
                    (station["name"],),
                )

            station["id"] = station_id[0][0]

        # Insert example symbols into the Symbols table
        symbols = [
            {"id": 1, "symb_name": "Symbol A"},
            {"id": 2, "symb_name": "Symbol B"},
        ]

        for symbol in symbols:
            symbol_id = run_get_cmd(
                "SELECT id FROM Symbols WHERE id = %s", (symbol["id"],)
            )
            if not symbol_id:
                run_exec_cmd(
                    """
                    INSERT INTO Symbols (id, symb_name)
                    VALUES (%s, %s)
                """,
                    (symbol["id"], symbol["symb_name"]),
                )

        # Additional example EOTRecords data for testing the SQL query
        new_eot_records = [
            # Fairport station, unit_addr 12345
            {
                "date_rec": "2025-04-04 10:10:00",
                "symbol_id": 1,
                "unit_addr": "12345",
                "brake_pressure": "80",
                "motion": "Yes",
                "marker_light": "On",
                "turbine": "Active",
                "battery_cond": "Good",
                "battery_charge": "90%",
                "arm_status": "Armed",
                "signal_strength": 75.0,
            },
            {
                "date_rec": "2025-04-04 12:00:00",
                "symbol_id": 1,
                "unit_addr": "12345",
                "brake_pressure": "85",
                "motion": "Yes",
                "marker_light": "On",
                "turbine": "Active",
                "battery_cond": "Good",
                "battery_charge": "95%",
                "arm_status": "Armed",
                "signal_strength": 80.0,
            },
            {
                "date_rec": "2025-04-04 14:00:00",
                "symbol_id": 1,
                "unit_addr": "12345",
                "brake_pressure": "90",
                "motion": "No",
                "marker_light": "Off",
                "turbine": "Inactive",
                "battery_cond": "Low",
                "battery_charge": "50%",
                "arm_status": "Disarmed",
                "signal_strength": 60.0,
            },
            # Churchville station, unit_addr 67890
            {
                "date_rec": "2025-04-04 11:00:00",
                "symbol_id": 2,
                "unit_addr": "67890",
                "brake_pressure": "70",
                "motion": "No",
                "marker_light": "Off",
                "turbine": "Inactive",
                "battery_cond": "Low",
                "battery_charge": "50%",
                "arm_status": "Disarmed",
                "signal_strength": 60.0,
            },
            {
                "date_rec": "2025-04-04 13:00:00",
                "symbol_id": 2,
                "unit_addr": "67890",
                "brake_pressure": "75",
                "motion": "Yes",
                "marker_light": "On",
                "turbine": "Active",
                "battery_cond": "Good",
                "battery_charge": "85%",
                "arm_status": "Armed",
                "signal_strength": 70.0,
            },
        ]

        # Insert new EOTRecords for each station
        for station in stations:
            for record in new_eot_records:
                # Assign the station ID to the record
                record["station_recorded"] = station["id"]
                run_exec_cmd(
                    """
                    INSERT INTO EOTRecords (date_rec, station_recorded, symbol_id, unit_addr, brake_pressure, motion, marker_light, turbine, battery_cond, battery_charge, arm_status, signal_strength)
                    VALUES (%(date_rec)s, %(station_recorded)s, %(symbol_id)s, %(unit_addr)s, %(brake_pressure)s, %(motion)s, %(marker_light)s, %(turbine)s, %(battery_cond)s, %(battery_charge)s, %(arm_status)s, %(signal_strength)s)
                """,
                    record,
                )

        # Print out all data from the database to verify
        all_stations = run_get_cmd("SELECT * FROM Stations")
        all_symbols = run_get_cmd("SELECT * FROM Symbols")
        all_eot_records = run_get_cmd("SELECT * FROM EOTRecords")

        print("Stations:")
        for station in all_stations:
            print(station)

        print("Symbols:")
        for symbol in all_symbols:
            print(symbol)

        print("EOT Records:")
        for record in all_eot_records:
            print(record)

        return {"message": "Example data loaded successfully"}, 200