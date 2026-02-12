from flask import Flask, Response, jsonify
from werkzeug.exceptions import HTTPException

from service.service_core import *

# A translation dictionary for Service layer exceptions
SERVICE_ERROR_CODES = {
    ServiceInvalidArgument: 400,
    ServiceResourceNotFound: 404,
    ServiceTimeoutError: 408,
    ServiceError: 500,
    ServiceInternalError: 500,
    ServiceParsingError: 500
}

def service_error_to_code(e: ServiceError) -> int:
    """Translates Service layer exceptions to the correct HTTP error response status code.

    Args:
        e (ServiceError): The Service layer exception to translate.

    Returns:
        int: HTTP error response status code.
    """
    for cls in e.__class__.__mro__:
        if cls in SERVICE_ERROR_CODES:
            return SERVICE_ERROR_CODES[cls]
    return 500
      

def handle_service_errors(e: ServiceError) -> Response:
    """Constructs a Flask *Response* for a provided Service layer exception.

    Args:
        e (ServiceError): A Service layer exception.

    Returns:
        Response: Constructs a Flask Response with the provided Service layer error message
        and error code.
    """
    return jsonify({"error": str(e)}), service_error_to_code(e)  


def handle_api_errors(e: HTTPException) -> Response:
    """Constructs a Flask *Response* for a provided HTTP exception.

    Args:
        e (HTTPException): An HTTPException.

    Returns:
        Response: Constructs a Flask Response with the provided HTTP exception description
        and code.
    """
    return jsonify({"error": e.description}), e.code    


def handle_other_errors() -> Response:
    """Constructs a Flask *Response* for unhandled/general Exceptions that may occur
    in the API.

    Returns:
        Response: Constructs a Flask Response with a general error message and code of 500.
    """
    return jsonify({"error": "Internal server error!"}), 500
        
        
def register_error_handlers(app: Flask):
    """Registers error handlers to a *Flask* instance which handle exceptions that occur
    in the API.

    Args:
        app (Flask): The main Flask instance the API is running on.
    """
    app.register_error_handler(ServiceError, handle_service_errors)
    app.register_error_handler(HTTPException, handle_api_errors)
    app.register_error_handler(Exception, handle_other_errors)