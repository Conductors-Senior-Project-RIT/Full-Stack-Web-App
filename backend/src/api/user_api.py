from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity, get_jwt, set_access_cookies, unset_jwt_cookies,
)
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, Unauthorized, NotFound, Forbidden
from dotenv import load_dotenv

from service.user_service import UserService
from backend.db import db

"""
TODO: mention below:
Switching security handling of passwords, easiest thing to do is for everyone to RESET THEIR PASSWORD
werkzeug is good enough security at the moment, future teams can switch back to bcrypt.
why? werkzeug doesn't require us to use another external dependency and don't have time to understand everything about bcrypt and I don't trust how the last group 
handled security as i had to rewrite most of what they did relating to jwt....

user_repo.py needs custom error handling so it can be caught here

storing jwt in database for "get_authentication" defeats the whole purpose of storing it securely with cookies (using the helper function from werkzeug security library)
"""

# bcrypt = Bcrypt()
jwt = JWTManager()

load_dotenv()
user_bp = Blueprint("user_bp", __name__)
CORS(user_bp)  # Enable CORS for the user_bp blueprint

"""
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
        return BadRequest("Email and password required")

    session = db.session
    service = UserService(session)

    result = service.register_user(email, password) #service

    if result.get("email_sent"):
        jsonify({"message": "User registered successfully! A welcome email has been sent."}), 201

    return jsonify({"message": "User registered, but failed to send email."}), 500

@user_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    session = db.session
    service = UserService(session)

    user = service.is_registered(email, password)
    if not user:
        raise Unauthorized("Invalid credentials")

    user_id = user[0][0] # need to find a clean way to stop double indexing, index the query results from the repo/db layer so we stop double indexing here.
    user_role = user[0][4]

    response = jsonify({"message": "login successful"}), 200

    additional_claims = {"user_role": user_role} # a user role is set based on what's in the database

    # identity being user_id makes it easier to retrieve user info from db for whatever reason, and can store their user_role here as it's not a security risk and makes it easier to protect certain routes later
    access_token = create_access_token(identity=str(user_id), additional_claims=additional_claims) # user_id as eventually want to replace incrementing id with uuid if possible
    set_access_cookies(response, access_token)
    return response

# the bottom 3 routes confuse me, need to look at frontend and see if i should remove one of the routes...
@user_bp.route("/api/forgot-password", methods=["POST"])
def reset_password_request():
    email = request.get_json()["email"]

    if not email:
        return BadRequest("Email is required!")

    session = db.session
    service = UserService(session)

    # we don't want to let the user now if an email exists or not (idk y but im following how this was done lol), so we handle email checking silently (return nothing)
    service.create_user_password_reset_token(email)

    return jsonify({"message": "If an account with that email exists, a reset link was sent."}), 200

@user_bp.route("/api/validate-reset-token", methods=["GET"])
def token_validation():
    token = request.args.get("token")
    
    session = db.session
    service = UserService(session)
    
    is_valid = service.is_user_password_reset_token_valid(token)

    if is_valid:
        return jsonify({"message": "Password reset token is valid"}), 200

    raise NotFound("Password reset token is invalid!")

@user_bp.route("/api/reset-password", methods=["PUT"])
def reset_password():
    token = request.args.get("token")

    if token is None:
        raise BadRequest("No token provided!") # by default this jsonify's the result i think? (we can test it out later so we can have a standard to follow for the returns in API layer)

    data = request.get_json()
    password = data.get("password")
    
    session = db.session
    service = UserService(session)

    result = service.reset_user_password(token, password) #again add custom error handling, don't want any of this "is none" or boolean checking

    # Is this the required payload?
    if not result:
        return {"valid": "false"}, 404

    return {"message": "Password changed successfully. Please log in."}, 200

# not sure why they're updating times for users... maybe ... what is the point of this lol /api/user_preferences/time
# delete this route?
@user_bp.route("/api/user_preferences/time", methods=["PUT"])
@jwt_required()
def update_times():
    current_user_id = int(get_jwt_identity()) # user_id is stored as a string for it to be an identity; so convert back to int
    data = request.get_json()
    starting_time = data.get("starting_time")
    ending_time = data.get("ending_time")

    if not starting_time or not ending_time:
        raise BadRequest("starting_time and ending_time required")

    session = db.session
    service = UserService(session)

    service.update_user_times(current_user_id, starting_time, ending_time)
    return jsonify({"message": "Success"}), 200


@user_bp.route("/api/role", methods=["GET"])
@jwt_required() # a user can only access this route with a jwt token and by default everyone has a role. so no way this throws an error ever... right? lol
def get_user_role():
    claims = get_jwt() # maybe current_user_* prefix is good when calling get_jwt() and get_jwt_identity()
    user_role = claims.get("user_role")
    return jsonify({"role": user_role}), 200

@user_bp.route("/api/elevate-user", methods=["PUT"])
@jwt_required()
def elevate_user():
    claims = get_jwt()
    user_role = claims.get("user_role")

    if user_role != 0: #admin role
        raise Forbidden("Unauthorized role")

    data = request.get_json()
    email_to_elevate = data.get("email")
    new_role = data.get("role")

    if new_role not in [1, 2]: # elevate user seems like a... not so accurate description for this route as it seems you can demote users to different roles as well?
        raise BadRequest("Invalid user role")

    session = db.session
    service = UserService(session)

    if service.update_account_status(email_to_elevate, new_role) is None: #if None is returned (again change all the "is None" with custom error handling...)
        return NotFound("The email you're trying to change roles for does not exist")

    return jsonify({"message": "User role updated successfully"}), 200

@user_bp.route("/api/logout", methods=["POST"])
@jwt_required()
def logout():
    response = jsonify({"message": "Logout successful"})
    unset_jwt_cookies(response)
    return response