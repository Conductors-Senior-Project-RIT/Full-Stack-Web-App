# Testing

## Brief Overview

Two kinds of tests live here:

- **`unittest.TestCase`** tests mocking everything (the db, other services), never touching a real db. Examples: `test_exceptions.py`, `test_train_history.py`.

- **`BaseTestCase`** tests run against a real (test db) Postgres database. Subclass this whenever a test actually needs to utilize a repository, service, or full route against real data.

`BaseTestCase` rebuilds a schema (`table.sql`) and reloads seed data (`test_data.sql`) before every test class, then wraps each individual test method in its own nested transaction that gets rolled back afterward — so tests in the same class can't leak state into each other even though they share one schema load.

`./run_test.sh` is just a thin 'wrapper script' around `python -m unittest` so you don't need it. Run tests however you'd normally invoke unittest (e.g. `python -m unittest backend.test.db.test_user_repo`). Put test specific config values like a separate test database URL in `.env.test` if needed.

## What's Missing
 
The Service, API, and Repository layers all lack testing. Testing `UserService` and `UserRepo` would be a great start to get familiar with the codebase.
 
Service Layer: `UserService` (possibly others too)
 
Repository Layer: `test_user_repo.py` has limited testing. 
 
API Layer: no tests yet for `user_api.py`, `user_preferences_api.py`, etc.
 
Worth going through `user_service.py` and `user_repo.py` to see what's tested vs. what's not, as its a crucial part of the web app.
 
## Integration Tests
 
A good scope for integration tests is when a lot of layers are working together. For example, does registration hash and persist a password correctly? The register endpoint interacts with multiple layers, so we test the result of those layers working together. 

## Coverage Reports

Use the `coverage` package to check testing coverage: https://coverage.readthedocs.io/en/7.15.4/#

Last thing I wanna say is use this general lack of testing to your advantage in understanding the codebase if possible. Good luck