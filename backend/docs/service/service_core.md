## Error Types {#s-error-types}
Below are the following exceptions that can be raised by any of the methods in this layer.

| Name | Description | `SError` |
|------|-------------|----------|
| `ServiceError` | Parent class for all errors in this layer. | N/A |
| `ServiceInternalError` | General errors that occur in the server. | `INTERNAL` |
| `ServiceTimeoutError` | Connection interruptions, timeouts, etc. | `TIMEOUT` |
| `ServiceParsingError` | Value parsing or indexing issues. | `PARSING` |
| `ServiceResourceNotFound` | Resource is not found such as a non-existing database row. | `NOT_FOUND` |
| `ServiceExistingResourceError` | New resource requests to be created but conflicts with an existing one. | `EXISTING` |
| `ServiceEmailError` | Error occurs when sending an email in [`EmailService`](email_service.md). | `EMAIL` |
| `ServiceInvalidArgument` | Invalid argument is provided. | `INVALID_ARG` |

## Service Error Mapping {#s-error-mapping}
All *SQLAlchemy*, *psycopg2*, and *Python* exceptions are caught by the error handling logic in [`ServiceErrorHandler`][src.service.service_core]. All error messages are set to be shown by default, it is the responsibility of the layers above to hide any messages from the client. Below are the current mappings present in the application, which can be extended or changed in the future (ie. translating built-in Python exceptions).

| Original | Translation | Shown |
|----------|-------------|-------|
| [`RepositorySessionError`][r-error-types] | [`ServiceInternalError`][s-error-types] | Yes |
| [`RepositoryExistingRowError`][r-error-types] | [`ServiceExistingResourceError`][s-error-types] | Yes |
| [`RepositoryParsingError`][r-error-types] | [`ServiceParsingError`][s-error-types] | No |
| [`RepositoryConnectionError`][r-error-types] | [`ServiceTimeoutError`][s-error-types] | No |
| [`RepositoryNotFoundError`][r-error-types] | [`ServiceResourceNotFound`][s-error-types] | Yes |
| [`RepositoryRecordInvalid`][r-error-types] | [`ServiceInvalidArgument`][s-error-types] | Yes |
| [`RepositoryInvalidArgumentError`][r-error-types] | [`ServiceInvalidArgument`][s-error-types] | Yes |
| [`RepositoryInternalError`][r-error-types] | [`ServiceInternalError`][s-error-types] | No |


::: src.service.service_core