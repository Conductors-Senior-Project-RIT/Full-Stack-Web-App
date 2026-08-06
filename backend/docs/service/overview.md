This layer encapsulates business logic and orchestrates repository operations. Various services exist in the application, which all process client requests specific to their domain. For instance, the [`UserService`](user_service.md) may need to access user and station data in the database in order to update the times at which a user prefers to receive station notifications. 
To interact with the database, this service instantiates both a *User* and *Station* repository to execute the necessary operations to accomplish this. If every action is successful, the service returns the parsed results back to the endpoint handler that called it in the [**API**]() layer. 

A service may need to process different kinds of database records that require the same processing strategies, such as signal/train records. In the domain of this application, these records exist in one of several forms: EOT, HOT, and DPU, which contain shared and distinct attributes. To facilitate this, the [`RecordService`](record_service.md) instantiates a [`RecordRepository`](../repository/record_repo.md) with the appropriate record and collation ORM models, specified by the client. Furthermore, some cases require this service to access all repositories in a single method. To accomplish this all repositories are created during instantiation and can be iterated over.

## Table of Contents

- [Service Core](service_core.md)
- [Record Service](record_service.md)
- [Station Service](station_service.md)
- [Symbol Service](symbol_service.md)
- [User Service](user_service.md)
- [Email Service](email_service.md)
