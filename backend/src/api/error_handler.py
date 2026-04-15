from flask import Flask, Response
from werkzeug.exceptions import HTTPException

from ...database import db
from ..service.service_core import *

##########################
##  API ERROR HANDLING  ##
##########################

# A translation dictionary for Service layer exceptions
SERVICE_ERROR_CODES = {
    ServiceInvalidArgument: 400,
    ServiceResourceNotFound: 404,
    ServiceExistingResource: 409,
    ServiceTimeoutError: 408,
    ServiceInternalError: 500,
    ServiceParsingError: 500,
    ServiceError: 500
}

def service_error_to_code(e: ServiceError) -> int:
    """Translates Service layer exceptions to the correct HTTP error response status code.

    Args:
        e (ServiceError): The Service layer exception to translate.

    Returns:
        int: HTTP error response status code.
    """
    # e.__class__.__mro__ returns the class hierarchy of the exception.
    # The following line locates the first class present in the error code map and returns its associated error code. The default value is 500.
    return next((SERVICE_ERROR_CODES[c] for c in e.__class__.__mro__ if c in SERVICE_ERROR_CODES), 500)
      

def handle_service_errors(e: ServiceError) -> Response:
    """Constructs a Flask `Response` for a provided Service layer exception.

    Args:
        e (ServiceError): A Service layer exception.

    Returns:
        Response: Constructs a Flask Response with the provided Service layer error message
        and error code.
    """
    # Rollback changes in the request's current session.
    db.session.rollback()
    
    # Return the corres.ponding error code if present
    return {"error": str(e)}, service_error_to_code(e)  


def handle_api_errors(e: HTTPException) -> Response:
    """Constructs a Flask `Response` for a provided HTTP exception.

    Args:
        e (HTTPException): An HTTPException.

    Returns:
        Response: Constructs a Flask Response with the provided HTTP exception description
        and code.
    """
    db.session.rollback()
    return {"error": e.description}, e.code    


def handle_other_errors(e: Exception) -> Response:
    """Constructs a Flask `Response` for unhandled/general Exceptions that may occur
    in the API.
    
    Args:
        e (Exception): A general Python exception.

    Returns:
        Response: Constructs a Flask Response with a general error message and code of 500.
    """
    db.session.rollback()
    if(TESTING_ENABLED): return {"error": e.args[0]}, 500
    return {"error": "Internal server error!"}, 500
        
        
def register_error_handlers(app: Flask):
    """Registers error handlers to a `Flask` instance which handle exceptions that occur
    in the API.

    Args:
        app (Flask): The main Flask instance the API is running on.
    """
    app.register_error_handler(ServiceError, handle_service_errors)
    app.register_error_handler(HTTPException, handle_api_errors)
    app.register_error_handler(Exception, handle_other_errors)
    