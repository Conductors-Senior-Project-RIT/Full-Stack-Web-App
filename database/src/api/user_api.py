import hashlib
import os
import requests
from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity, get_jwt, set_access_cookies, unset_jwt_cookies,
)
from flask_cors import CORS
from db.user_db import *
from dotenv import load_dotenv
import secrets

from service.user_service import register_user, is_registered

bcrypt = Bcrypt()
jwt = JWTManager()

load_dotenv()
user_bp = Blueprint("user_bp", __name__)
CORS(user_bp)  # Enable CORS for the user_bp blueprint

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
WEBSITE_DOMAIN = os.getenv("WEBSITE_DOMAIN")

"""
api routes should be thin
read request (maybe simply input validation) --> call service --> translate service result --> http response  

files/functionality to divide:
* email_service for emails
* user_service

lets ditch the storing session token from database... im not sure why they did that as it beats the purpose of using
jwt lol.

TODO: need to create a decorator to place on routes that only admins should be able to touch 
TODO: refresh token 30 mins before it expires (check docs where it uses an `after_request` callback)
@app.after_request
def refresh_expiring_jwts(response)
"""
@user_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() # frontend's mimetype indicates JSON
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email and password required"}), 500

    try:
        result = register_user(email, password) #service
    except Exception as e:
        return jsonify({"message": str(e)}), 500 # use derived error message since an error can come from a few different sources

    if result.get("email_sent"):
        jsonify({"message": "User registered successfully! A welcome email has been sent."}), 201

    return jsonify({"message": "User registered, but failed to send email."}), 500

@user_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = is_registered(email, password) # need to find a clean way to stop double indexing, db models should help with this but cant do it now

    if not user:
        return jsonify({"message": "Invalid credentials"}), 401

    user_id = user[0][0]
    user_role = user[0][4]

    response = jsonify({"msg": "login successful"})
    additional_claims = {"user_role": user_role} # a user role is set based on what's in the database
    # identity being user_id makes it easier to retrieve user info from db for whatever reason, and can store their user_role here as it's not a security risk and makes it easier to protect certain routes later
    access_token = create_access_token(identity=str(user_id), additional_claims=additional_claims) # user_id as eventually want to replace incrementing id with uuid if possible
    set_access_cookies(response, access_token)
    return response

@user_bp.route("/api/forgot-password", methods=["POST"])
def reset_password_request():
    email = request.get_json()["email"]
    results = get_user_id(email)
    print(results)
    # Response will return the same way regardless if the email actually exists, but it won't be sent if it won't
    # exist
    if not results:
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
#
# never used and again, this can be handled by jwt-flask library -- will delete later and replace this!

#
# @user_bp.route("/api/validate-reset-token", methods=["GET"])
# def token_validation():
#     token = request.args.get("token")
#     token_hash = hashlib.sha256(token.encode()).hexdigest()
#     validate_token_sql = """
#     SELECT * FROM reset_requests as r
#     INNER JOIN users AS u ON r.uid = u.id
#     WHERE r.token = %(token_hash)s AND r.expiration >= NOW();
#     """
#     results = run_get_cmd(validate_token_sql, args={"token_hash": token_hash})
#     if len(results) == 0:
#         return {"valid": "false"}, 404
#
#     return {"valid": "true"}, 200


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
    update_user_password(userId, hashed_password)

    delete_request = "DELETE FROM reset_requests WHERE uid = %(user_id)s;"
    run_exec_cmd(delete_request, args={"user_id": userId})

    return {"message": "Password changed successfully. Please log in."}, 200

# not sure why they're updating times for users... maybe ... what is the point of this lol /api/user_preferences/time
# delete this route?
@user_bp.route("/api/user_preferences/time", methods=["PUT"])
@jwt_required()
def update_times():
    current_user = get_jwt_identity()
    token = request.headers.get("Authorization").split()[1]
    user = get_authenticated_user(current_user, token)
    if user:
        user_id = user[0][0]
        data = request.get_json()
        update_user_times(user_id, data["starting_time"], data["ending_time"])
        return jsonify({"message": "Success"}), 200
    else:
        return jsonify({"message": "Error saving times"}), 500


@user_bp.route("/api/role", methods=["GET"])
@jwt_required() # a user can only access this route with a jwt token and by default everyone has a role. so no way this throws an error ever... right? lol
def get_user_role():
    claims = get_jwt()
    user_role = claims.get("user_role")
    return jsonify({"role": user_role}), 200

@user_bp.route("/api/elevate-user", methods=["PUT"])
@jwt_required()
def elevate_user():
    claims = get_jwt()
    user_role = claims.get("user_role")

    if user_role != 0: #admin role
        return jsonify({"message": "Unauthorized role"}), 403

    data = request.get_json()
    email_to_elevate = data.get("email")
    new_role = data.get("role")

    if new_role not in [1, 2]: # elevate user seems like a... not so accurate description for this route as it seems you can demote users to different roles as well?
        return jsonify({"message": "Invalid role"}), 400

    if not update_account_status(email_to_elevate, new_role): #if None is returned
        return jsonify({"message": "The email you're trying to change role's for does not exist in our database"}), 404

    return jsonify({"message": "User role updated successfully"}), 200

@user_bp.route("/api/logout", methods=["POST"])
@jwt_required()
def logout():
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response