from functools import wraps
from typing import Type
from backend import error_debugging


class LayerError(Exception):
    "Parent class for exceptions that occur in any of the backend layers."
    
    # Default message of a layer error, can be changed by child exceptions.
    default_message = "Unknown error occurred!"

    def __init__(
            self,
            caller_name: str | None = None,
            poe: str | None = None,
            message: str | None = None,
            show_error=False,
            cause: Exception | None = None
    ):
        """Constructor for a `LayerError` instance.
    
        The contents of a message includes the following:
        - An optional caller prefix in the format `[caller_name]`
        - A public-facing message, either the class's `default_message` or,
        if debugging is enabled, the location and details of the error.

        Args:
            caller_name (str | None, optional): Name of the caller (typically a class) 
                used as a prefix for the error message with, e.g. the name of the service 
                or component raising the exception. Defaults to None.
            poe (str | None, optional): Point of error that identifies where in the
                code the exception was raised, e.g. a function or method name.
                Only included in the message when debugging is enabled.
                Defaults to None.
            message (str | None, optional): A detailed error message with
                specifics about the failure. Only added to the public message
                when debugging is enabled (via `error_debugging` in app creation) or
                `show_error`. Defaults to None.
            show_error (bool, optional): If `True`, forces the detailed error
                message and point of error to be shown regardless of the global
                `error_debugging` flag. Defaults to False.
            cause (Exception | None, optional): The exception that is the cause of this error. If provided, this exception is attached 
                to the `LayerError` instance via `__cause__` chaining, allowing for preservation 
                of the original exceptions and their tracebacks. Defaults to None.
        """
        # Contruct the caller prefix and point of error message if provided
        caller = f"[{caller_name}] " if caller_name else ""
        point_of_error = f"Exception raised in {poe}! " if poe else ""

        # Construct the body of the error message based on parameters provided
        # Set the initial message to an error's default message
        public = self.default_message
        
        # If the app is in debugging mode or the error has been explicitly set to 
        # display, and a message has been provided, construct the error message accordingly.
        if (error_debugging or show_error) and message:
            # Display the specific error message if provided, followed by the default message and additional error details.
            public = f"{point_of_error}{public.rstrip(".!")}: {message}"
        
        # Attach the cause for exception for later reference
        self.cause = cause
        
        # Pass the final error message to the Exception constructor
        super().__init__(f"{caller}{public}")
        
    def __cause__(self) -> Exception | None:
        """Override the default cause behavior to return exception if provided."""
        return getattr(self, 'cause', None)

def layer_error_handler(
        error_map: dict[Exception | tuple[Exception], tuple[Exception, bool]],
        base_exception: Type[LayerError],
        exclude: tuple[Type[Exception]] | Type[Exception] | None = None,
        message: str | None = None
):
    """Decorator used to provide error translation for exceptions thrown in the backend layers.

    Wraps a function with a general-purpose error-handling strategy, catching exceptions and
    translating them into layer-specific errors via a provided error map. Any exception not
    covered by `error_map` or the `exclude` is caught and re-raised as the provided
    `base_exception` or itself, respectively. Preserves the original exception as the cause via 
    `raise ... from e`.

    Args:
        error_map (dict[Exception | tuple[Exception], tuple[Exception, bool]]): A mapping of
            source exception type(s) to a tuple of `(Exception, bool)`, where the bool
            indicates whether the translated error should provide specifics in its message.
            Both single exception types and tuples of exception types are valid as keys, allowing
            multiple exceptions to map to the same target. Broader exceptions (such as top-level parent exceptions) 
            should be placed lower in the map because translation works by selecting the first match.

            Example:
            {
                (TimeoutError, UnboundExecutionError): (RepositoryConnectionError, False),
                (TypeError, KeyError, IndexError): (RepositoryParsingError, False),
                SQLAlchemyError: (RepositoryInternalError, False)
            }

        base_exception (Type[LayerError]): The fallback exception type raised when a caught
            exception has no matching entry in `error_map`. Ensures unhandled exceptions are 
            still wrapped in a layer-appropriate error to prevent leaking lower-level 
            implementation details.

        exclude (tuple[Type[Exception]] | Type[Exception] | None, optional): An exception type
            or tuple of exception types that should be ignored in translation entirely. Useful for 
            allowing certain exceptions to propagate without interference (eg. a `LayerError` 
            is raised in its own layer). Defaults to None.

        message (str | None, optional): A custom message to attach to the translated exception.
            If None, the message defaults to a string of the form `"ExceptionType: exception message"`,
            derived from the caught exception. Defaults to None.

    Raises:
        `LayerError` (or subclass): Raises a translated exception determined by `error_map`, using
            `base_exception` as the fallback if no mapping is found. The original exception is
            always chained via `raise ... from e` to preserve the traceback and root cause.

        `Exception` (if ignored): If the raised exception matches a type in `exclude`, it is
            re-raised immediately without translation.

    Returns:
        `function`: The original function wrapped with exception handling logic with its signature and 
        metadata preserved.

    Notes:
        - The caller's class name and function name are automatically captured and passed to
          `translate_error` to help with error context.
        - The inner `decorator` uses `*args` and assumes `args[0]` is the instance of the class whose 
        method is being wrapped via `self`. This decorator is therefore intended for use on instance methods, 
        not standalone functions.
    """
    def wrapper(func):
        @wraps(func)
        def decorator(*args, **kwargs):
            # Reference the instance calling the function
            caller_name = args[0].__class__.__name__ if args else None
            
            try:
                # Return the wrapped function in the try/except
                return func(*args, **kwargs)
            except Exception as e:
                # Immediately raise the error if its type should be ignored during translation
                if exclude and isinstance(e, exclude):
                    raise e

                # Translate the respective exception to the correct type.
                # Any exception in 'exclude' has been handled, so passing it into translation is unecessary
                error = translate_error(
                    e,
                    error_map,
                    base_exception,
                    caller_name,
                    func.__name__,
                    f"{type(e).__name__}: {e}" if not message else message
                )
                
                # Raise the error using 'from' to preserve traceback and root cause information
                raise error from e
        
        return decorator
    return wrapper


def translate_error(
        e: Exception,
        error_map: dict[Exception | tuple[Exception], tuple[Exception, bool]],
        base_exception: Type[LayerError],
        caller_name: str | None = None,
        point_of_error: str | None = None,
        message: str | None = None,
        exclude: tuple[Type[Exception]] | Type[Exception] | None = None
) -> LayerError | Exception:
    """Translates a provided `Exception` instance using a map potential exception classes.
    
    Uses general-purpose error-handling logic to produce layer-specific errors. Any exception not
    covered by `error_map` is translated to a fallback exception provided in `base_exception`. All 
    exceptions with a matching type in `exclude` is returned as-is.

    Args:
        e (Exception): See `layer_error_handler` for details.
        
        base_exception (Type[LayerError]): See `layer_error_handler` for details.
        
        caller_name (str | None, optional): Defaults to None. See `layer_error_handler` for details.

        point_of_error (str | None, optional): Specifies the exception's origin location. The point
            of error will be displayed in the error's message to be used for debugging purposes, providing error
            context. Defaults to None.
        
        message (str | None, optional): See `layer_error_handler` for details. Defaults to None.
        
        exclude (tuple[Type[Exception]] | Type[Exception] | None, optional): See `layer_error_handler` for details. 
            Defaults to None.

    Returns:
        LayerError | Exception: If a matching translation is found in `error_map`, a subclass instance of `LayerError`
            is returned. In the case a match is not found, the class provided in `base_exception` is instantiated and 
            returned as a fallback, preventing lower-level implementation details from propagating upwards. If the 
            provided exception `e` is an instance with a matching type in `exclude`, it is returned as-is.
    """
    # Return the exception if its type exists in exclusion list
    if exclude and isinstance(e, exclude):
        return e
    
    # Find the first matching type in the error map. Returns a tuple containing an exception class,
    # and a boolean that determines whether previous exception details should be propogated. 
    # If a match is not found, None is returned.
    error_class = next((error_map[cls] for cls in error_map if isinstance(e, cls)), None)

    if error_class:
        layer_exception, show_error = error_class

        # Return a new LayerError instance with the provided details
        return layer_exception(
            caller_name,
            poe=point_of_error,
            message=message,
            show_error=show_error,
            cause=e
        )

    # Match not found, instantiate and return the fallback exception
    return base_exception(
            caller_name,
            poe=point_of_error,
            message=message,
            show_error=show_error,
            cause=e
        )