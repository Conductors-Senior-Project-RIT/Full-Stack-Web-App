# Service Overview

This layer encapsulates business logic and orchestrates repository operations. Various services exist in the application, which all process client requests specific to their domain. For instance, the [`UserService`](#userservice) may need to access user and station data in the database in order to update the times at which a user prefers to receive station notifications. 
To interact with the database, this service instantiates both a *User* and *Station* repository to execute the necessary operations to accomplish this. If every action is successful, the service returns the parsed results back to the endpoint handler that called it in the **API** layer. 

A service may need to process different kinds of database records that require the same processing strategies, such as signal/train records. In the domain of this application, these records exist in one of several forms: EOT, HOT, and DPU, which contain shared and distinct attributes. To facilitate this, the [`RecordService`](#record-service) instantiates a `RecordRepository` with the appropriate record and collation ORM models, specified by the client. Furthermore, some cases require this service to access all repositories in a single method. To accomplish this all repositories are created during instantiation and can be iterated over.

Currently, *five* services exist in the application, four of which extend [`BaseService`](#base-service) in [`service.service_core`](#service-core). The [`EmailService`](#emailservice) class does not require error handling functionality, as it is does not interact with any other layers.

![Service Diagram](./diagrams/service.png)
**The class diagram above provides a somewhat simplified overview for the connected components in this layer.**

# Service Core

## Base Service
The purpose of `BaseService` is to provide a sublcass constructor for services that should be wrapped with the application's error handling logic using `wrap_error_handler` (see [Error Handling](errors.md)). Extending this class removes the need to manually integrate layer-specific exception handling for each method.

## Service Error Handling
This layer employs the standardized functionality from `global_core.exceptions` to translate `RepositoryError` exceptions into [`ServiceError`](#error-types) exceptions. Additionally, this layer should specify the set of exceptions allowed to display their error messages to the **API** layer and client. To achieve this, the [`SERVICE_ERROR_MAP`](#repository-to-service-mapping) is used, where the key specifies the exception being translated, and the tuple contains the new exception along with a boolean indicating whether the error message should be shown in the response. If the *Flask* instance is in either testing or debugging mode, all error messages will be displayed, regardless of the current settings in the error map.

## Error Types

| Name | Description |
|------|-------------|
| `ServiceError` | Parent class for all errors in this layer. |
| `ServiceInternalError` | General errors that occur in the server. |
| `ServiceTimeoutError` | Connection interruptions, timeouts, etc. |
| `ServiceParsingError` | Value parsing or indexing issues. |
| `ServiceResourceNotFound` | Resource is not found such as a non-existing database row. |
| `ServiceExistingResourceError` | New resource requests to be created but conflicts with an existing one. |
| `ServiceInvalidArgument` | Invalid argument is provided. |

## Repository to Service Mapping

| Original | Translation | Shown |
|----------|-------------|-------|
| `RepositorySessionError` | `ServiceInternalError` | Yes |
| `RepositoryExistingRowError` | `ServiceExistingResourceError` | Yes |
| `RepositoryParsingError` | `ServiceParsingError` | No |
| `RepositoryConnectionError` | `ServiceTimeoutError` | No |
| `RepositoryNotFoundError` | `ServiceResourceNotFound` | Yes |
| `RepositoryRecordInvalid` | `ServiceInvalidArgument` | Yes |
| `RepositoryInvalidArgumentError` | `ServiceInvalidArgument` | Yes |
| `RepositoryInternalError` | `ServiceInternalError` | No |



# RecordService

Handles business logic for signal/train record related data processing. Inherits [`BaseService`](#base-service).

## \_\_init\_\_

Upon initialization, a `RecordRepository` is instantiated using the provided `record_type`. Uses `get_record_repository` or `get_all_repositories` if `record_type` is `None`, which are factory functions in `db.record_types` designed for `RecordRepository` initialization. Repositories are always stored in a list; use `get_first_repository` to access the repository passed in through the constructor. The service instance is initialized with a SQLAlchemy session to be shared across all repository instances.

## get_train_history

## post_train_history

### check_recent_notification

### add_new_pin

### attempt_auto_fill

## signal_update

## get_collated_records

## verify_record

## time_frame_pull


# StationService

## get_stations

## update_station_password

## generate_password_string

## get_last_seen

## update_last_seen

## format_date


# SymbolService
Not much currently, but might be very useful in the future for symbol tracking.

## get_symbol

## create_symbol


# UserService

# EmailService


