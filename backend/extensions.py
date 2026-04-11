from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_restful import Api

api = Api()
bcrypt = Bcrypt()
jwt = JWTManager()