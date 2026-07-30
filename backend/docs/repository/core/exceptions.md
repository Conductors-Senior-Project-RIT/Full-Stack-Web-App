## Error Types {#error-types}
Below are the following exceptions that can be raised by any of the methods in this layer.

| Name | Description | `RError` |
|------|-------------|----------|
| `RepositoryError` | Parent class for all errors in this layer. | N/A |
| `RepositorySessionError` | An error occurs with a session in the repository, or is not provided during the instantiation of a repository. | `SESSION` |
| `RepositoryConnectionError` | Connection interruptions, timeouts, etc. | `CONNECTION` |
| `RepositoryParsingError` | Value parsing, indexing issues, or problem constructing a valid query. | `PARSING` |
| `RepositoryNotFoundError` | Resource is not found such as a non-existing database row. | `NOT_FOUND` |
| `RepositoryExistingRowError` | New resource requests to be created but conflicts with an existing one. | `EXISTING` |
| `RepositoryInvalidArgumentError` | Invalid argument is provided. | `INVALID_ARG` |
| `RepositoryRecordInvalid` | Invalid record train type is provided. | `INVALID_RECORD` |
| `RepositoryInternalError` | An unknown exception raised in the layer. | `INTERNAL` |

## Repository Error Mapping {#error-mapping}
All *SQLAlchemy*, *psycopg2*, and *Python* exceptions are caught by the error handling logic in [`RepositoryErrorHandler`][src.db.db_core.exceptions.RepositoryErrorHandler]. All error messages are set to be shown by default, it is the responsibility of the layers above to hide any messages from the client. Below are the current mappings present in the application, which can be extended or changed in the future.

| Original | Translation |
|----------|-------------|
| `TimeoutError`, `UnboundExecutionError`, `InterfaceError`, `NoSuchModuleError` | [`RepositoryConnectionError`](#error-types) |
| `NoResultFound` | [`RepositoryNotFoundError`](#error-types) |
| `MultipleResultsFound`, `UniqueViolation` | [`RepositoryExistingRowError`](#error-types) |
| `TypeError`, `KeyError`, `ValueError`, `IndexError`, `ZeroDivisionError`, `DataError`, `ProgrammingError`, `IntegrityError` | [`RepositoryParsingError`](#error-types) |
| `SQLAlchemyError` | [`RepositoryInternalError`](#error-types) |

::: src.db.db_core.exceptions