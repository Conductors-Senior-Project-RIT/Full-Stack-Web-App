# User Endpoints

A majority, if not all of these endpoints handle account registration, login/logout, password resets, and role management.

## Background Info

`Users` table backs authentication and stores the following (check [`UserRepository`][src.db.user_repo] for some queries):

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer | Primary key. |
| `email` | string | Normalized, unique. Used as the login identifier. |
| `passwd` | string | Bcrypt hash. Never returned to the client. |
| `acc_status` | integer | The user's role. Admin: `0`, Volunteer: `1`, Regular user: `2`. |
| `starting_time` / `ending_time` | string | Notification window for train alerts. |

A related `UserPreferences` table stores `(user_id, station_id)` rows for which stations a user wants alerts from, and a `reset_requests` table stores hashed password reset tokens

**Typical User Auth flow:**

1. `POST /register` hashes the password, inserts the user, sets up default preferences, and sends a welcome email. 
2. `POST /login` verifies the email/password against the stored hash, then issues a JWT. The JWT's identity is the user's `id` and it carries the user's `acc_status` as a `user_role` claim, so role checks don't need a database hit.
3. On every response, [`register_jwt_access_token_refresh`](./core/decorators.md) checks if the token is within 30 minutes of expiring and silently reissues one if so, so an active user is never logged out mid session.
4. `POST /logout` just clears the cookie, there's no server side token blacklist.

Almost all routes use the [`role_required`](./core/decorators.md) decorator. 

## POST `/api/register`

Registers a new user.

Uses [`UserService`][src.service.user_service.UserService].

### Body Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `email` | string | Yes | The account email. |
| `password` | string | Yes | Plaintext password, hashed before storage. |

### Example

```json
{
    "email": "example@email.com",
    "password": "hunter2"
}
```

Returns `201` with a confirmation message on success. Raises `BadRequest` if either field is missing, or a service layer error if the email is already registered.

## POST `/api/login`

Authenticates a user and sets a JWT access cookie.

Uses [`UserService`][src.service.user_service.UserService].

### Body Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `email` | string | Yes | The account email. |
| `password` | string | Yes | Plaintext password to verify. |

Returns `200` and sets the `access_token_cookie` on success. Raises `Unauthorized` if the email/password combination is invalid.

## POST `/api/logout`

Clears the JWT access cookie. Requires a valid JWT (`@role_required()`).

Returns `200` with a confirmation message.

## GET `/api/role`

Returns the role of the currently authenticated user, read from the JWT claims (no database call, checks additional_claims within jwt token). Requires a valid JWT.

### Example Response

```json
{
    "role": 2
}
```

## POST `/api/forgot-password`

Requests a password reset. Always returns `200` with a generic message whether or not the email exists, so the endpoint can't be used to enumerate registered accounts.

Uses [`UserService`][src.service.user_service.UserService].

### Body Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `email` | string | Yes | The email to send a reset link to, if it exists. |

## GET `/api/validate-reset-token`

Checks whether a password reset token is valid and unexpired.

### Query Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `token` | string | Yes | The raw reset token from the emailed link. |

Returns `200` if valid, or raises `NotFound` if the token is invalid/expired.

## PUT `/api/reset-password`

Resets a user's password using a valid reset token. Deletes the token on success so it can't be reused.

Uses [`UserService`][src.service.user_service.UserService].

### Query Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `token` | string | Yes | The raw reset token from the emailed link. |

### Body Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `password` | string | Yes | The new plaintext password. |

Raises `BadRequest` if the token or password is missing, or `NotFound` if the token doesn't correspond to a valid reset request.

## PUT `/api/elevate-user`

Updates another user's role. Admin only (`@role_required(0)`).

Uses [`UserService`][src.service.user_service.UserService].

### Body Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `email` | string | Yes | The email of the account whose role is changing. |
| `role` | integer | Yes | The new role: Admin `0`, Volunteer `1`, Regular user `2`. |

## PUT `/api/user_preferences/time`

Updates the notification start/end time window for the authenticated user.

Uses [`UserService`][src.service.user_service.UserService].

### Body Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `starting_time` | string | Yes | Start of the notification window. |
| `ending_time` | string | Yes | End of the notification window. |