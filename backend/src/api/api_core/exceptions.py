import json

from flask import Flask, Response, make_response, jsonify
from werkzeug.exceptions import HTTPException

from ....database import db
from ...service.service_core import SError as SE
from ...service.service_core import ServiceError

##########################
##  API ERROR HANDLING  ##
##########################

# A translation dictionary for Service layer exceptions
# TODO: ApiError can be thrown from brev python sdk in email_service so maybe thats something for me to add later here

SERVICE_ERROR_CODES = {
    SE.INVALID_ARG: 400,
    SE.NOT_FOUND: 404,
    SE.TIMEOUT: 408,
    SE.EXISTING: 409,
    SE.PARSING: 500,
    SE.INTERNAL: 500
}

def service_error_to_code(e: ServiceError) -> int:
    """Translates [`ServiceError`][s-error-types] exceptions to the 
    correct HTTP error response status code.

    Args:
        e (ServiceError): The Service layer exception to translate.

    Returns:
        (int): HTTP error response status code.
    """
    # e.__class__.__mro__ returns the class hierarchy of the exception.
    # The following line locates the first class present in the error code map and returns its associated error code. The default value is 500.
    return next((SERVICE_ERROR_CODES[c] for c in e.__class__.__mro__ if c in SERVICE_ERROR_CODES), 500)
      

def handle_service_errors(exception: ServiceError) -> Response:
    """Constructs a 
    Flask [`Response`](https://flask.palletsprojects.com/en/stable/api/#flask.Response) 
    for a provided [ServiceError][s-error-types] exception.

    Args:
        exception (ServiceError): A Service layer exception.

    Returns:
        (Response): Constructs a response with the provided Service layer error message
            and error code.
    """
    # Rollback changes in the request's current session.
    db.session.rollback()
    
    # TODO: Implement logging in the future
    print(str(exception))
    
    # Return the corres.ponding error code if present
    return make_response({"error": str(exception)}, service_error_to_code(exception))


def handle_api_errors(exception: HTTPException) -> Response:
    """Constructs a 
    Flask [`Response`](https://flask.palletsprojects.com/en/stable/api/#flask.Response) 
    for a provided [`HTTPException`](https://werkzeug.palletsprojects.com/en/stable/exceptions/).

    Args:
        exception (HTTPException): An `HTTPException`.

    Returns:
        (Response): Constructs a response with the provided HTTP exception description
            and status code.
    """
    db.session.rollback()
    
    # TODO: Implement logging in the future
    print(str(exception))
    
    return make_response({"error": exception.description}, exception.code)


def handle_other_errors(exception: Exception) -> Response:
    """Constructs a 
    Flask [`Response`](https://flask.palletsprojects.com/en/stable/api/#flask.Response) 
    for unhandled/general Exceptions that may occur in the API.
    
    Args:
        exception (Exception): A general Python exception.

    Returns:
        (Response): Constructs a response with a general error message and status 
            code of 500.
    """
    from backend import error_debugging
    
    db.session.rollback()
    
    # TODO: Implement logging in the future
    print(str(exception))
    
    if(error_debugging): 
        return make_response({"error": exception.args[0]}, 500)
    else:
        return make_response({"error": "Internal error occurred!"}, 500)


def register_error_handlers(app: Flask):
    """Registers error handlers to a [`Flask`](https://flask.palletsprojects.com/en/stable/api/#flask.Flask) 
    instance which handle exceptions that occur in the API.

    Args:
        app (Flask): The main Flask instance the API is running on.
    """
    app.register_error_handler(ServiceError, handle_service_errors)
    app.register_error_handler(HTTPException, handle_api_errors)
    app.register_error_handler(Exception, handle_other_errors)
    