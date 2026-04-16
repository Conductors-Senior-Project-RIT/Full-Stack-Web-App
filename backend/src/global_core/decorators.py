from functools import wraps

from flask_jwt_extended import get_jwt, verify_jwt_in_request, create_access_token, get_jwt_identity, set_access_cookies

from werkzeug.exceptions import Forbidden
from datetime import datetime
from datetime import timedelta
from datetime import timezone

"""
At the moment: Helpful decorators for API 
"""

def role_required(*allowed_roles): 
    """
    Flask route decorator: can be used to verify user has a jwt in the request + their jwt has a claim indicating the user's role status
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request() 
            user_role = get_jwt().get("user_role")
            if user_role not in allowed_roles:
                raise Forbidden("Insufficient permissions to access route")
            return fn(*args, **kwargs)
        return decorator
    return wrapper


# at the end of EVERY request, check if JWT is close to expiring, we refresh any token that is within 30
# minutes of expiring. Change the timedeltas to match the needs of your application.
def register_jwt_access_token_refresh(app):
    @app.after_request
    def refresh_expiring_jwts(response):
        try:
            exp_timestamp = get_jwt()["exp"]
            user_role = get_jwt()["user_role"]

            now = datetime.now(timezone.utc)
            target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
            if target_timestamp > exp_timestamp:
                additional_claims = {"user_role": user_role}  # preserve role when refreshing access token
                access_token = create_access_token(identity=get_jwt_identity(), additional_claims=additional_claims)
                set_access_cookies(response, access_token)
            return response
        except (RuntimeError, KeyError):
            # Case where there is not a valid JWT. Just return the original response
            return response
