from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from service.service_core import *

SERVICE_ERROR_CODES = {
    ServiceInvalidArgument: 400,
    ServiceResourceNotFound: 404,
    ServiceTimeoutError: 408,
    ServiceError: 500,
    ServiceInternalError: 500,
    ServiceParsingError: 500
}

def service_error_to_code(e: ServiceError):
    for cls in e.__class__.__mro__:
        if cls in SERVICE_ERROR_CODES:
            return SERVICE_ERROR_CODES[cls]
    return 500
      

def handle_service_errors(e: ServiceError):
        return jsonify({"error": str(e)}), service_error_to_code(e)  


def handle_api_errors(e: HTTPException):
        return jsonify({"error": e.description}), e.code    


def handle_other_errors(e):
        return jsonify({"error": "Internal server error!"}), 500
        
def register_error_handlers(app: Flask):
    app.register_error_handler(ServiceError, handle_service_errors)
    app.register_error_handler(HTTPException, handle_api_errors)
    app.register_error_handler(Exception, handle_other_errors)