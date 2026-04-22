from flask import Blueprint, request, make_response
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity, get_jwt, set_access_cookies, unset_jwt_cookies,
)

from backend.src.global_core.decorators import role_required
from ..service.user_service import UserService
from werkzeug.exceptions import BadRequest, Unauthorized, NotFound
# from ..service.email_service import email_service 
from backend.database import db

"""
auth rewritten,  using cookies to handle jwt 

app.config["JWT_TOKEN_LOCATION"] = ["cookies"] --> is easer than [headers] but if can't complete will rollback to headers to be compatabile with app
app.config["JWT_SECRET_KEY"] = "super-secret"
app.config["JWT_COOKIE_SECURE"] = False
app.config["JWT_COOKIE_CSRF_PROTECT"] --> since using cookies 
"""

user_bp = Blueprint("user_bp", __name__)
@user_bp.route("/api/register", methods=["POST"]) # works
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
    
    additional_claims = {"user_role": user_role} # a user role is set based on what's in the database
    # lookup partial loading with identity -> can be cleaner and less db operations as specific user model can be stored
    access_token = create_access_token(identity=str(user_id), additional_claims=additional_claims) # user_id as eventually want to replace incrementing id with uuid if possible
    
    response = make_response({"message": "login successful"}, 200)

    set_access_cookies(response, access_token) 

    # session.commit()
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
    claims = get_jwt() # maybe current_user_* prefix is good when calling get_jwt() and get_jwt_identity()
    user_role = claims.get("user_role")
    return {"role": user_role}, 200

# first here 
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

# thirdly
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

    session.commit()

    raise NotFound("Password reset token is invalid!")

#secondly
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
        raise NotFound ("Issue resetting password")

    session.commit()
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
    
    session.commit()
    return {"message": "Success"}, 200


@user_bp.route("/api/elevate-user", methods=["PUT"])
@role_required(0) # admin only
def elevate_user():
    # claims = get_jwt()
    # user_role = claims.get("user_role")

    # if user_role != 0: #admin role
    #     raise Forbidden("Unauthorized role")

    data = request.get_json()
    email_to_elevate = data.get("email")
    new_role = data.get("role")

    # if new_role not in [1, 2]: # elevate user seems like a... not so accurate description for this route as it seems you can demote users to different roles as well?
    #     raise BadRequest("Invalid user role")

    session = db.session
    service = UserService(session)

    service.update_user_role(email_to_elevate, new_role) #if None is returned (again change all the "is None" with custom error handling...)
        # return NotFound("The email you're trying to change roles for does not exist")

    session.commit()
    return {"message": "User role updated successfully"}, 200

