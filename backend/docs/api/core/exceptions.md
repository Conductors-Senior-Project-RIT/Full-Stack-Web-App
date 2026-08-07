Various errors raised in the **API** or [**Service**](../../service/overview.md) layers are caught by their appropriate error handlers in [`api_core.exceptions`][src.api.api_core.exceptions], which then constructs a response payload depending on the exception raised. The API layer employs a **WSGI** library, **Werkzeug**, for raising exceptions that occur directly within the layer, such as in cases of invalid arguments or permissions. Every [`HTTPException`](https://werkzeug.palletsprojects.com/en/stable/exceptions/) maps directly its appropriate status code through the [`handle_api_errors`][src.api.api_core.exceptions.handle_api_errors] error handler.

Every derivation of a [`ServiceError`][s-error-types] is mapped to a different HTTP status code, defined by a dictionary [`SERVICE_ERROR_CODES`](#service-error-codes). When one of these exceptions arrive at the API layer, the [`handle_service_errors`][src.api.api_core.exceptions.handle_service_errors] handler constructs the appropriate payload.

## Service Error Codes

| Name | [`SError`][s-error-types] | Status Code |
| ---- | ------------------------- | ----------- |
| `ServiceInvalidArgument` | `INVALID_ARG` | *400* |
| `ServiceResourceNotFound` | `NOT_FOUND` | *404* |
| `ServiceTimeoutError` | `TIMEOUT` | *408* |
| `ServiceExistingResourceError` | `EXISTING` | *409* |
| `ServiceParsingError` | `PARSING` | *500* |
| `ServiceInternalError` | `INTERNAL` | *500* |

## Error Response Payload

All error responses include the same payload structure:

```json
{
    "error": string
}
```

::: src.api.api_core.exceptions
