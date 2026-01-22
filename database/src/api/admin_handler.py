from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import CORS
from src.db.trackSense_db_commands import *

admin_bp = Blueprint("admin_bp", __name__)
CORS(admin_bp)  # Enable CORS for the admin_bp blueprint


@admin_bp.route("/api/add-pin", methods=["POST"])
@jwt_required()
def add_pin():
    data = request.get_json()
    lat = data.get("lat")
    lng = data.get("lng")

    if lat is None or lng is None:
        return jsonify({"message": "Invalid data"}), 400

    # Insert the pin into the database
    run_exec_cmd("INSERT INTO Pins (lat, lng) VALUES (%s, %s)", (lat, lng))
    return jsonify({"message": "Pin added successfully"}), 201


@admin_bp.route("/api/get-pins", methods=["GET"])
def get_pins():
    pins = run_get_cmd("SELECT lat, lng FROM Pins")
    return jsonify([{"lat": pin[0], "lng": pin[1]} for pin in pins])
