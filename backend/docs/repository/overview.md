This layer aims to provide an interface for database access. It utilizes SQLAlchemy’s Object Relational Mapping (ORM) library to provide a robust system for mapping Python model objects to database tables (see ORM Models). We utilize SQLAlchemy’s query construction interface to perform operations on pre-defined models that track the changes made in a database session. Another benefit of ORMs is that they reduce the refactoring effort required when switching database technologies by abstracting query construction, generating and executing service-specific SQL from model definitions at runtime.

As previously mentioned, changes can either be committed to the database if successful or rolled back in the case of an error, offering an effective way to properly manage client-server transactions. However, this layer should only be responsible for flushing its changes to the session; the **API** layer should be the final decider on whether changes should be reverted or persisted to the database. When a repository method is successful and that method's query returns a model or `Row`, that data is converted to a dictionary representation for consistency, removing additional coupling with the layer above. 

![Repository-Diagram](../diagrams/repository.png)

## Table of Contents
- Core
    - [Models](core/models.md)
    - [Exceptions](core/exceptions.md)
    - [Repository](core/repository.md)
- Record Repository
- Station Repository
- Symbol Repository
- User Repository