One of our goals for the refactoring process was to construct a standardized error handling system that would propagate exceptions through the chain of layers. Such a system will allow future developers to easily attach error handling to new features, expose only necessary details of lower-level exceptions in production environments, permit full error traceability in development environments, and group similar errors into generalized layer exceptions. 

To achieve this, we incorporate Python’s function decorators to wrap class methods across the layers with an error translation mechanism. Any exceptions raised in a decorated function would immediately be mapped to a layer-specific error through translation. When an exception moves from the [**Service**]() layer to the [**API**](), the response receives a status code and an error message that is either generalized or specific, depending on the exception provided and the Flask environment that was created.

The code for the error handling is located in the `global_core.exceptions` module, and can be used in any of the layers. The [**API**]() layer uses the error handlers provided by *Flask*, but the [**Service**]() and [**Repository**](../repository/core/exceptions.md) layers utilize the error handling logic described here.

## Type Aliases {#eh-alias}

### `ExceptionType`
Indicates that either a single `Exception` or a tuple of `Exception` classes is accepted.

**Example:**
```python
# Both are valid
example1: ExceptionType = TypeError
example2: ExceptionType = (TypeError, ValueError)

```

### `ErrorMapping`
A dictionary in which a key, represented by an `ExceptionType`, is mapped to an `Exception` class along with a boolean value indicating whether an error message should be displayed.

In the example below, a `NotImplementedError` should be mapped to an `ArgumentError`, with its error message displayed publicly. Conversely, `TypeError` and `ValueError` exceptions should be mapped to a `ParsingError`, which does not publicly display its error message.

**Example:**

```python
class ArgumentError(LayerError):
    pass

class ParsingError(LayerError):
    pass

mapping = {
    NotImplementedError: (ArgumentError, True),
    (TypeError, ValueError): (ParsingError, False)
}
```


::: src.global_core.exceptions