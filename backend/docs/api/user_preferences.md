# User Preferences Endpoints

Endpoints for a user's station preferences and notification window

## GET `/api/user_preferences`
 
Retrieves the authenticated user's station preferences and notification time window.
 
Uses [`UserService`][src.service.user_service.UserService].
 
Requires a valid JWT. The user is identified from the JWT, not a request parameter.
 
### Response 200
 
| Name | Type | Description |
|------|------|-------------|
| `station_id` | integer | The station's ID. |
| `station_name` | string | The station's name. |
| `selected` | boolean | Whether the user is currently subscribed to this station. |
| `start_time` | string | Start of the user's notification window, formatted `HH:MM`. |
| `end_time` | string | End of the user's notification window, formatted `HH:MM`. |
 
Response is a list containing items per station adjusted to user's notification liking
 
## POST `/api/user_preferences`
 
Replaces the authenticated user's full list of station preferences. Existing preferences are deleted before the new list is inserted.
 
Uses [`UserService`][src.service.user_service.UserService].
 
Requires a valid JWT.
 
### Body Parameters
 
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `preferences` | list of integers | No | Station IDs to subscribe to. Defaults to `[]`, which clears all preferences. |
 
### Response 200
 
| Name | Type | Description |
|------|------|-------------|
| `message` | string | Confirms preferences were updated. |