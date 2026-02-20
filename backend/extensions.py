from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_restful import Api
#following docs to avoid circular imports
api = Api()
bcrypt = Bcrypt()
jwt = JWTManager()