import hashlib
import os
import requests
from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from flask_cors import CORS
from db.trackSense_db_commands import *
from dotenv import load_dotenv
import secrets

bcrypt = Bcrypt()
jwt = JWTManager()

load_dotenv()
user_bp = Blueprint("user_bp", __name__)
CORS(user_bp)  # Enable CORS for the user_bp blueprint

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
WEBSITE_DOMAIN = os.getenv("WEBSITE_DOMAIN")


@user_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")

    # Hash the user's password
    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    # Insert the new user into the Users table
    run_exec_cmd(
        "INSERT INTO Users (email, passwd) VALUES (%s, %s)",
        (email, hashed_password),
    )
    # Remove this for now.
    #
    # response = requests.post(
    #     f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
    #     auth=("api", MAILGUN_API_KEY),
    #     data={
    #         "from": f"Follow That FRED! <no-reply@{MAILGUN_DOMAIN}>",
    #         "to": email,
    #         "subject": "Welcome to Our App!",
    #         "text": f"Hi {email},\n\nThank you for registering with our app! We're excited to have you on board.\n\nBest regards,\nThe Team",
    #     },
    # )

    # Fetch the newly created user's ID
    user = run_get_cmd("SELECT id FROM Users WHERE email = %s", (data["email"],))
    if not user:
        return jsonify({"message": "Error creating user"}), 500

    user_id = user[0][0]

    # Fetch all station IDs from the Stations table
    stations = run_get_cmd("SELECT id FROM Stations")
    if not stations:
        return jsonify({"message": "No stations available to subscribe to"}), 500

    # Insert all stations into the UserPreferences table for the new user
    for station in stations:
        station_id = station[0]
        run_exec_cmd(
            "INSERT INTO UserPreferences (user_id, station_id) VALUES (%s, %s)",
            (user_id, station_id),
        )

    return (
        jsonify(
            {
                "message": "User registered successfully!"
            }
        ),
        201,
    )


@user_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    user = run_get_cmd("SELECT * FROM Users WHERE email = %s", (data["email"],))
    if user and bcrypt.check_password_hash(user[0][2], data["password"]):
        access_token = create_access_token(identity=str(user[0][1]))
        run_exec_cmd(
            "UPDATE Users SET token = %s WHERE id = %s", (access_token, user[0][0])
        )
        return jsonify({"access_token": access_token})
    else:
        return jsonify({"message": "Invalid credentials"}), 401


@user_bp.route("/api/verify-token", methods=["POST"])
@jwt_required()
def verify_token():
    current_user = get_jwt_identity()
    token = request.headers.get("Authorization").split()[1]
    user = run_get_cmd(
        "SELECT * FROM Users WHERE email = %s AND token = %s", (current_user, token)
    )
    if user:
        return jsonify({"valid": True})
    else:
        return jsonify({"valid": False}), 401


@user_bp.route("/api/forgot-password", methods=["POST"])
def reset_password_request():
    email = request.get_json()["email"]
    check_email = "SELECT id FROM users WHERE email = %s"
    results = run_get_cmd(check_email, (email,))
    print(results)
    # Response will return the same way regardless if the email actually exists, but it won't be sent if it won't
    # exist
    if len(results) > 0:
        userId = results[0][0]
        reset_token = secrets.token_urlsafe(32)
        print(reset_token)
        hashed_token = hashlib.sha256(reset_token.encode()).hexdigest()
        reset_token_sql = """
        INSERT INTO reset_requests (uid, token, expiration) VALUES 
        (%(user_id)s, %(token_hash)s, NOW() + INTERVAL '1 hour');
        """
        run_exec_cmd(
            reset_token_sql, args={"user_id": userId, "token_hash": hashed_token}
        )
        requests.post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            data={
                "from": f"Follow That FRED! <no-reply@{MAILGUN_DOMAIN}>",
                "to": email,
                "subject": "Password Reset Request",
                "text": f"""Hi {email},\n\nA password reset request was made from your account. If you wish to reset your password, please click the following link: {WEBSITE_DOMAIN}/reset-password?token={reset_token} \n\nIf you did not request to reset your password, please disregard this email.""",
                "html": f"<html><body><h3>Hi {email},</h3>\n\n<p>A password reset request was made from your account. If you wish to reset your password, please click the following link: {WEBSITE_DOMAIN}/reset-password?token={reset_token} \n\nIf you did not request to reset your password, please disregard this email.</p></body></html>",
            },
        )

    data = {"message": "If an account with that email exists, a reset link was sent."}
    return data, 200


@user_bp.route("/api/validate-reset-token", methods=["GET"])
def token_validation():
    token = request.args.get("token")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    validate_token_sql = """
    SELECT * FROM reset_requests as r
    INNER JOIN users AS u ON r.uid = u.id
    WHERE r.token = %(token_hash)s AND r.expiration >= NOW();
    """
    results = run_get_cmd(validate_token_sql, args={"token_hash": token_hash})
    if len(results) == 0:
        return {"valid": "false"}, 404

    return {"valid": "true"}, 200


@user_bp.route("/api/reset-password", methods=["PUT"])
def reset_password():
    token = request.args.get("token")
    if token is None:
        return {"msg": "No token provided"}, 400
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    validate_token_sql = """
        SELECT u.id FROM reset_requests as r
        INNER JOIN users AS u ON r.uid = u.id
        WHERE r.token = %(token_hash)s AND r.expiration >= NOW();
    """
    results = run_get_cmd(validate_token_sql, args={"token_hash": token_hash})
    if len(results) == 0:
        return {"valid": "false"}, 404

    userId = results[0][0]
    update_password_sql = (
        "UPDATE users SET passwd = %(passwd_hash)s WHERE id = %(user_id)s;"
    )
    run_exec_cmd(
        update_password_sql, args={"passwd_hash": hashed_password, "user_id": userId}
    )

    delete_request = "DELETE FROM reset_requests WHERE uid = %(user_id)s;"
    run_exec_cmd(delete_request, args={"user_id": userId})

    return {"message": "Password changed successfully. Please log in."}, 200


@user_bp.route("/api/user_preferences/time", methods=["PUT"])
@jwt_required()
def update_times():
    current_user = get_jwt_identity()
    token = request.headers.get("Authorization").split()[1]
    user = run_get_cmd(
        "SELECT * FROM Users WHERE email = %s AND token = %s", (current_user, token)
    )
    if user:
        sql = """
            UPDATE Users
            SET starting_time = %(start_time)s,
            ending_time = %(ending_time)s
            WHERE id = %(uid)s
        """
        uid = user[0][0]
        data = request.get_json()
        args = {
            "start_time": data["starting_time"],
            "ending_time": data["ending_time"],
            "uid": uid,
        }
        run_exec_cmd(sql, args=args)
        return jsonify({"message": "Success"}), 200
    else:
        return jsonify({"message": "Error saving times"}), 500
    
@user_bp.route("/api/role", methods=["GET"])
@jwt_required()
def get_user_role():
    current_user = get_jwt_identity()
    token = request.headers.get("Authorization").split()[1]
    user = run_get_cmd(
        "SELECT acc_status FROM Users WHERE email = %s AND token = %s",
        (current_user, token),
    )
    if user:
        return jsonify({"role": user[0][0]}), 200
    else:
        return jsonify({"message": "Invalid user or token"}), 401


@user_bp.route("/api/elevate-user", methods=["PUT"])
@jwt_required()
def elevate_user():
    current_user = get_jwt_identity()
    token = request.headers.get("Authorization").split()[1]
    user = run_get_cmd(
        "SELECT acc_status FROM Users WHERE email = %s AND token = %s",
        (current_user, token),
    )
    if user and user[0][0] == 0:
        data = request.get_json()
        email_to_elevate = data.get("email")
        new_role = data.get("role")
        if new_role not in [1, 2]:
            return jsonify({"message": "Invalid role"}), 400

        run_exec_cmd(
            "UPDATE Users SET acc_status = %s WHERE email = %s",
            (new_role, email_to_elevate),
        )
        return jsonify({"message": "User role updated successfully"}), 200
    else:
        return jsonify({"message": "Unauthorized"}), 403
