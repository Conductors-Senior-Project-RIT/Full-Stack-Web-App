from functools import wraps
import sys
from typing import Optional, Type, TypeAlias, Union
import inspect

ExceptionType: TypeAlias = Union[Type[Exception], tuple[Type[Exception], ...]]
ErrorMapping: TypeAlias = dict[ExceptionType, tuple[Type[Exception], bool]]

class LayerError(Exception):
    """Parent class for exceptions that occur in any of the backend layers."""

    # Default message of a layer error, can be changed by child exceptions.
    default_message = "Unknown error occurred!"

    def __init__(
        self,
        caller_name: Optional[str] = None,
        poe: Optional[str] = None,
        message: Optional[str] = None,
        show_error: bool = False,
        cause: Optional[Exception] = None,
    ):
        """Constructor for a `LayerError` instance.
        The contents of a message include the following:
        - An optional caller prefix in the format `[caller_name]`
        - A public-facing message, either the class's `default_message` or, if 
        debugging is enabled, the location and details of the error.
        
        Args:
            caller_name (str, optional): Name of the caller (typically a class) used as
                a prefix for the error message, e.g., the name of the service or
                component raising the exception. Defaults to None.
            poe (str, optional): Point of error that identifies where in the code the
                exception was raised, e.g., a function or method name. Only included in
                the message when debugging is enabled. Defaults to None.
            message (str, optional): A detailed error message with specifics about the
                failure. Only added to the public message when debugging is enabled (via
                `error_debugging` in app creation) or `show_error`. Defaults to None.
            show_error (bool): If True, forces the detailed error message and point of
                error to be shown regardless of the global `error_debugging` flag.
                Defaults to False.
            cause (Exception, optional): The exception that is the cause of this error.
                If provided, this exception is attached to the LayerError instance.
                Defaults to None.
        """
        # Prevent circular import
        from backend import error_debugging

        # Attach the cause exception for later reference
        self.cause = cause
        
        # Construct the body of the error message based on parameters provided
        public = self._build_public(poe, message, show_error, cause, error_debugging)
        
        # Construct the final message
        final = f"[{caller_name}] {public}" if caller_name else public
        super().__init__(final)


    def _build_public(self, poe, message, show_error, cause, error_debugging) -> str:
        # Set the initial message to the error's default message
        if not (error_debugging or show_error) or not message:
            return self.default_message

        # If the app is in debugging mode or the error has been explicitly set to
        # display, and a message has been provided, construct the error message accordingly.
        body = self._build_body(message, error_debugging, cause)
        
        # Construct the caller prefix and point of error message if provided
        prefix = f"Exception raised in {poe}! " if poe and error_debugging else ""
        
        # Display the specific error message if provided, followed by the default message and additional error details.
        return f"{prefix}{body}"


    def _build_body(self, message, error_debugging, cause) -> str:
        # If message is not a string, attempt to convert it to a string for display.
        # If this fails, default to an empty message.
        new_message = message if isinstance(message, str) else str(message)

        if not error_debugging:
            # This removes any existing "[LayerError]: " prefix from the original
            # message to avoid exposing lower level details.
            idx = message.find("]")
            new_message = message[idx + 2:] if idx > 0 else new_message
            
        if cause and not isinstance(cause, LayerError):
            new_message += f" | {type(cause).__name__}: {cause}" 
            
            
        return new_message

    def __cause__(self) -> Exception | None:
        """Override the default cause behavior to return exception if provided."""
        return getattr(self, "cause", None)
    

class ErrorHandlingConfig:
    """Configuration class for layer error handling."""
    error_map: ErrorMapping = {}  # Default ignores translation
    base_exception: Type[LayerError] = LayerError  # Default translates all exceptions to LayerError
    exclude: ExceptionType = LayerError  # Any LayerErrors raised will be ignored

 
class LayerErrorHandler(ErrorHandlingConfig):
    error_origin_name: Optional[str]  = None
    
    @classmethod
    def wrap_error_handler(
        cls,
        func,
        message: Optional[str] = None,
    ):
        """Wraps a function with a general-purpose error-handling strategy.

        Catches exceptions and translates them into layer-specific errors via a provided
        error map. Any exception not covered by `error_map` or the `exclude` is caught and 
        re-raised as the provided `base_exception` or itself, respectively. Preserves the 
        original exception as the cause via `raise ... from e`.

        Args:
            error_map (ErrorMapping): A dictionary mapping of exception translations. Both 
                single exception types and tuples of exception types are valid as keys, 
                allowing multiple exceptions to map to the same target. Broader exceptions 
                should be placed lower in the map because translation works by selecting the 
                first match. See `ErrorMapping` for the required structure.
            base_exception (Type[LayerError]): The fallback exception type raised when a
                caught exception has no matching entry in `error_map`. Ensures unhandled
                exceptions are still wrapped in a layer-appropriate error to prevent leaking
                lower-level implementation details.
            exclude (ExceptionType, optional): An exception type or tuple of exception types
                that should be ignored in translation entirely. Useful for allowing certain
                exceptions to propagate without interference. Defaults to None.
            message (str, optional): A custom message to attach to the translated exception.
                If None, the message defaults to a string of the form `"ExceptionType:
                exception message"`. Defaults to None.

        Returns:
            function: The original function wrapped with exception handling logic with its
                signature and metadata preserved.

        Raises:
            `LayerError`: Raises a translated exception determined by `error_map`, using
                    `base_exception` as the fallback if no mapping is found.
            `Exception`: If the raised exception matches a type in `exclude`, it is
                    re-raised immediately without translation.
            `Notes`: * The caller's class name and function name are automatically captured
                    and passed to `translate_error`. * The inner `decorator` uses `*args`
                    and assumes `args[0]` is the instance of the class (`self`). This is
                    intended for instance methods.

        Example Error Map:
            ```
            ```python
            error_map = {
                (TimeoutError, UnboundExecutionError): (RepositoryConnectionError, False),
                (TypeError, KeyError, IndexError): (RepositoryParsingError, False),
                SQLAlchemyError: (RepositoryInternalError, False)
            }
            ```
            ```
        """

        @wraps(func)
        def decorator(*args, **kwargs):
            # Reference the instance calling the function
            func_name = getattr(func, "__name__", repr(func))
            # Rename constructor function name
            func_name = "initialization" if func_name == "__init__" else func_name
            
            # Get the class that called the function
            caller_name = args[0].__class__.__name__ if args else None

            try:
                # Return the wrapped function in the try/except
                return func(*args, **kwargs)
            except Exception as e:
                # Immediately raise the error if its type should be ignored during translation
                if cls.exclude and isinstance(e, cls.exclude):
                    raise e

                # Translate the respective exception to the correct type.
                # Any exception in 'exclude' has been handled, so passing it into translation is unecessary
                error = cls.translate_error(
                    e,
                    caller_name,
                    func_name,
                    f"{type(e).__name__}: {e}" if not message else message,
                )

                # Raise the error using 'from' to preserve traceback and root cause information
                raise error from e

        return decorator

    @classmethod
    def layer_error_decorator(
        cls,
        message: Optional[str] = None,
    ):
        """Decorator to provide error translation for exceptions in backend layers.

        See `translate_error` for details on the error-handling strategy. This decorator is
        applied to instance methods to automatically catch exceptions, translate them into
        layer-specific errors using an `error_map`, and re-raise them while preserving the
        original exception as the cause.

        Args:
            error_map (ErrorMapping): A mapping of source exception type(s) to a tuple of
                `(Exception, bool)`.
            base_exception (Type[LayerError]): The fallback exception type.
            exclude (ExceptionType, optional): Exceptions to ignore. Defaults to None.
            message (str, optional): A custom error message. Defaults to None.

        Returns:
            callable: The original function wrapped with exception handling logic, with its
                signature and metadata preserved.

        Raises:
            `LayerError`: A translated exception determined by `error_map`, using
                    `base_exception` as the fallback.
            `Exception`: If the exception matches a type in `exclude`, it is re-raised
                    immediately.
            `Note`: See `wrap_error_handler` for details on the parameters, which are passed
                    directly to the inner error-handling logic.

        Examples:
            ```
            Default parameters:
            ```python
            @layer_error_handler(error_map={}, base_exception=RepositoryInternalError)
            def example_method(self):
                ...
            ```
            ```

            ```
            Custom parameters:
            ```python
            @layer_error_handler(
                error_map={
                    TypeError: (RepositoryParsingError, False),
                    (ConnectionError, BufferError): (RepositoryConnectionError, False)
                },
                base_exception=RepositoryInternalError,
                exclude=RepositoryError,
                message="An error occurred!"
            )
            def some_repository_method(self):
                ...
            ```
            ```
        """

        # Python decorators implicitly pass the function to wrap as an argument to `wrapper`.
        def wrapper(func):
            return cls.wrap_error_handler(func, message)

        return wrapper

    @classmethod
    def translate_error(
        cls,
        exc: Exception,
        caller_name: Optional[str] = None,
        point_of_error: Optional[str] = None,
        message: Optional[str] = None,
    ) -> LayerError | Exception:
        """Translates a provided `Exception` instance using a map potential exception classes.

        Uses general-purpose error-handling logic to produce layer-specific errors. Any
        exception not covered by `error_map` is translated to a fallback exception provided
        in `base_exception`. All exceptions with a matching type in `exclude` is returned
        as-is.

        Args:
            exc (Exception): The exception instance that will be translated. If its type does 
                not correspond with a matching translation in `error_map`, or it has a matching 
                type in `exclude`, the exception is returned as-is.
            error_map (ErrorMapping): A dictionary mapping of exception translations. Both single 
                exception types and tuples of exception types are valid as keys, allowing multiple 
                exceptions to map to the same target. Broader exceptions should be placed lower in 
                the map because translation works by selecting the first match.
            base_exception (Type[LayerError]): The fallback exception type raised when a caught 
                exception has no matching entry in `error_map`. Ensures unhandled exceptions are 
                still wrapped in a layer-appropriate error to prevent leaking lower-level 
                implementation details.
            caller_name (str, optional): Name of the caller (typically a class) used as a prefix for 
                the error message, e.g., the name of the service or repository raising the exception. 
                Defaults to None.
            point_of_error (str, optional): Point of error that identifies where in the code the 
                exception was raised, e.g., a function or method name. Only included in the message 
                when debugging is enabled. Defaults to None.
            message (str, optional): A custom message to attach to the translated exception. If None, 
                the default message in the `LayerError` is used. Defaults to None.
            exclude (ExceptionType, optional): An exception type or tuple of exception types that 
                should be ignored in translation entirely. Useful for allowing certain exceptions to 
                propagate without interference. Defaults to None.

        Returns:
            LayerError | Exception: If a matching translation is found in `error_map`, a `LayerError` 
                instance is returned. In the case a match is not found, the class provided in 
                `base_exception` is instantiated and returned as a fallback, preventing lower-level 
                implementation details from propagating upwards. If the provided exception `e` is an 
                instance with a matching type in `exclude`, it is returned as-is.
        """
        # Return the exception if its type exists in exclusion list
        if cls.exclude and isinstance(exc, cls.exclude):
            return exc

        # Find the first matching type in the error map. Returns a tuple containing an exception class,
        # and a boolean that determines whether previous exception details should be propogated.
        # If a match is not found, None is returned.
        error_class = None
        for err in cls.error_map:
            # If the provided exception has an origin attribute matching a key in the error map, then search that first
            origin = None if cls.error_origin_name is None else getattr(exc, cls.error_origin_name, None)
            if origin:
                error_class = next((cls.error_map[sub_err] for sub_err in cls.error_map if isinstance(origin, sub_err)), None)
                if error_class:
                    break
            
            # If either the exception itself does not contain an origin attribute or it doesn't have a matching entry, search the error map directly
            if isinstance(exc, err):
                error_class = cls.error_map[err]
                break   

        if error_class:
            layer_exception, show_error = error_class

            # Return a new LayerError instance with the provided details
            return layer_exception(
                caller_name=caller_name,
                poe=point_of_error,
                message=message,
                show_error=show_error,
                cause=exc,
            )

        # Match not found, instantiate and return the fallback exception
        return cls.base_exception(
            caller_name, poe=point_of_error, message=message, show_error=False, cause=exc
        )

class LayerErrorWrapper:
    """A superclass for wrapping class methods with layer error handling."""
    error_handler: Type[LayerErrorHandler] = LayerErrorHandler
    
    def __init_subclass__(cls, **kwargs) -> None:
        """Wraps the methods in a subclass with the error handling."""
        super().__init_subclass__(**kwargs)
        cls._wrap_class()
        
    @classmethod
    def _wrap_class(cls):
        """`cls` should be a subclass extending `LayerErrorWrapper`."""
        for name, value in cls.__dict__.items():
            # Ensure that the value is a function; otherwise, attributes and other things will be ignored
            if not inspect.isfunction(value):
                continue
            
            # Wrap the current method (value) if it hasn't already been wrapped
            if not getattr(value, "_is_wrapped", False):             
                wrapped = cls.error_handler.wrap_error_handler(value)
                wrapped._is_wrapped = True
                setattr(cls, name, wrapped)
                
                
class LayerErrorInvoker:
    error_handler: Type[LayerErrorHandler] = LayerErrorHandler
    
    def _raise(self, error_class: type[LayerError], message, show_error=False, cause=None, depth=1):
        raise error_class(
            caller_name=self.__class__.__name__,
            poe=sys._getframe(depth).f_code.co_name,
            message=message,
            show_error=show_error,
            cause=cause
        )
        
    def _validate(self, condition, error_class, message, show_error=False):
        if not condition:
            self._raise(error_class, message, show_error, depth=2)
            
    def _translate_and_raise(self, e: Exception, error_message, depth=1):
        err = self.error_handler.translate_error(
            exc=e, 
            caller_name=self.__class__.__name__,
            point_of_error=sys._getframe(depth).f_code.co_name,
            message=error_message
        )
        raise err from e
            