from flask import Blueprint, request, make_response
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity, get_jwt, set_access_cookies, unset_jwt_cookies,
)

from backend.src.global_core.decorators import role_required
from ..service.user_service import UserService
from werkzeug.exceptions import BadRequest, Unauthorized, NotFound
from backend.database import db

user_bp = Blueprint("user_bp", __name__)
@user_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() # frontend's mimetype indicates JSON
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        raise BadRequest("Email and password required")

    session = db.session
    service = UserService(session)
    service.register_user(email, password) 

    session.commit()
    # Temporarily allow email sending to fail until we recreate the email sending functionality.
    # raise InternalServerError("User registered, but failed to send email.")

    return {"message": "User registered. Please check your email for a message from us shortly. If you don't see it,  check your spam folder and mark it as not spam."}, 201

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

    user_id = user.get("id")
    user_role = user.get("acc_status")
    
    additional_claims = {"user_role": user_role}
    access_token = create_access_token(identity=str(user_id), additional_claims=additional_claims)
    
    response = make_response({"message": "login successful"}, 200)

    set_access_cookies(response, access_token)
    return response

@user_bp.route("/api/logout", methods=["POST"])
@role_required()
def logout():
    response = make_response({"message": "logout successful"}, 200)
    unset_jwt_cookies(response)
    return response

@user_bp.route("/api/role", methods=["GET"])
@role_required()
def get_user_role():
    claims = get_jwt()
    user_role = claims.get("user_role")
    return {"role": user_role}, 200

@user_bp.route("/api/forgot-password", methods=["POST"])
def reset_password_request():
    email = request.get_json()["email"]

    if not email:
        raise BadRequest("Email is required!")

    session = db.session
    service = UserService(session)
    service.create_user_password_reset_token(email)

    session.commit()
    return {"message": "If an account with that email exists, a reset link was sent."}, 200

@user_bp.route("/api/validate-reset-token", methods=["GET"])
def token_validation():
    token = request.args.get("token")
    
    if not token:
        raise BadRequest("no token provided!")

    session = db.session
    service = UserService(session)
    is_valid = service.is_user_password_reset_token_valid(token) 

    if is_valid:
        return {"message": "Password reset token is valid"}, 200

    raise NotFound("Password reset token is invalid!")

@user_bp.route("/api/reset-password", methods=["PUT"])
def reset_password():
    data = request.get_json()
    password = data.get("password")
    
    token = request.args.get("token")

    if token is None:
        raise BadRequest("No token provided!")
    
    if not password:
        raise BadRequest("No password provided!")

    session = db.session
    service = UserService(session)
    if not service.reset_user_password(token, password):
        raise NotFound("Issue resetting password")

    session.commit()
    return {"message": "Password changed successfully. Please log in."}, 200

@user_bp.route("/api/user_preferences/time", methods=["PUT"])
@jwt_required()
def update_times():
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    starting_time = data.get("starting_time")
    ending_time = data.get("ending_time")

    if not starting_time or not ending_time:
        raise BadRequest("starting_time and ending_time required")

    session = db.session
    service = UserService(session)
    service.update_user_times(current_user_id, starting_time, ending_time) 
    
    session.commit()
    return {"message": "Success"}, 200


@user_bp.route("/api/elevate-user", methods=["PUT"])
@role_required(0) # admin only
def elevate_user():
    data = request.get_json()
    email_to_elevate = data.get("email")
    new_role = data.get("role")

    session = db.session
    service = UserService(session)
    service.update_user_role(email_to_elevate, new_role)

    session.commit()
    return {"message": "User role updated successfully"}, 200

