from functools import wraps
from typing import Type
import os

TESTING_ENABLED = os.environ.get("FLASK_APP_ENV", "dev") != "prod" # hide internal error details in prod

class LayerError(Exception):
    default_message = "Unknown error occurred!"

    def __init__(
            self,
            caller_name: str | None = None,
            poe: str | None = None,
            message: str | None = None,
            show_error=False
    ):
        caller = f"[{caller_name}] " if caller_name else ""
        point_of_error = f"Exception raised in {poe}! " if poe else ""

        public = self.default_message
        if (TESTING_ENABLED or show_error) and message:
            public = f"{point_of_error}{public.rstrip('.')}: {message}"
        super().__init__(f"{caller}{public}")

def layer_error_handler(
        func,
        error_map: dict,
        base_exception: Type[LayerError],
        exclude: tuple[Type[Exception]] | Type[Exception] | None = None,
        message: str | None = None
):
    """This function acts as a decorator to provide Service layer error translation for
    Repository layer errors that are raised.

    Args:
        func (`function`): The function to wrap with error handling in the Service layer.

    Raises:
        `ServiceError`: Raises a corresponding ServiceError depending on the RepositoryError
        raised. A ServiceInternalError is raised in the case of an unspecified base Exception.

    Returns:
        `function`: Returns a function wrapped with RepositoryError handling.
    """

    @wraps(func)
    def decorator(*args, **kwargs):
        # Reference the Service instance calling the function
        caller_name = args[0].__class__.__name__
        try:
            # Return our wrapped function
            return func(*args, **kwargs)
        except Exception as e:
            if not exclude or isinstance(e, exclude):
                raise e

            error = translate_error(
                e,
                error_map,
                base_exception,
                caller_name,
                func.__name__,
                f"{type(e).__name__}: {e}" if not message else message
            )
            raise error from e
        
    return decorator


def translate_error(
        e: Exception,
        error_map: dict,
        base_exception: Type[LayerError],
        caller_name: str | None = None,
        point_of_error: str | None = None,
        message: str | None = None
) -> LayerError:
    error_class = next((error_map[cls] for cls in error_map if isinstance(e, cls)), None)

    if error_class:
        layer_exception, show_error = error_class

        return layer_exception(
            caller_name,
            poe=point_of_error,
            message=message,
            show_error=show_error
        )

    return base_exception(caller_name) 