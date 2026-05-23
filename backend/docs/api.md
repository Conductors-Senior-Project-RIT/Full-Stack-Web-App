# API Overview

Our application leverages **Flask** and **SQLAlchemy**, which are the two key libraries to handle HTTP request and define when database transactions begin and end. The API layer defines the various endpoints, contains the Flask route handlers responsible for parsing requests and responses, and creates request-specific databases session to be used by the layers below.

A request starts when the API layer receives and validates client request parameters in an endpoint handler. If the parameters are valid, a *scoped session* is instantiated through a `sessionmaker`, which can be accessed by `db.session` in the `backend.database` module after a Flask application context is created.

Promptly after a session is created, it is provided with additional necessary data to an appropriate Service Layer module to process the request. If an error does not occur in any of the layers below, all changes in the session are then persisted in the database and the resulting data is sent back to the client in a response payload. Errors that propagate to the API layer are processed by a corresponding error handler in `api_core.exceptions`, which revert any changes made in the database session, returning a proper error response to the client.

*Notes*:
- All API endpoints start with the `/api` prefix.*
- All request and response bodies are in JSON format.

![Request_Sequence](./diagrams/request_seq.png)
**The sequence diagram above illustrates the processes involved in both successful and failed client requests.**

## Error Responses

Various errors raised in the **API** or **Service** layers are caught by their appropriate error handlers in `api_core.exceptions`, which then construct a response payload depending on the exception raised. The API layer employs a **WSGI** library, **Werkzeug**, for raising exceptions that occur directly within the layer, such as in cases of invalid arguments or permissions. Every `HTTPException` maps directly its appropriate status code through the `handle_api_errors` error hanndler.

Every derivation of a `ServiceError` is mapped to a different HTTP status code, defined by a dictionary `SERVICE_ERROR_CODES` in `api_core.exceptions`. When one of these exceptions arrive to the API layer, the `handle_service_errors` handler constructs the appropriate payload.

All error reponses include the same payload structure:
```json
{
    "error": string
}
```

# Volunteer Endpoints

These endpoints can only be accessed by users with *Volunteer* or *Admin* permissions. The `role_required` decorator in `api_core.decorators` can be applied to a Flask route to restrict access to authorized users only.

**Example Route:**

```python
@example_blueprint.get("/api/example")
@role_required(0, 1)
def get_records():
    ...
```

**Example Resource:**

```python
class Example(Resource):
    @role_required(0, 1)
    def get(self):
        ...
```

## GET `/symbols`

Retrieves a symbol ID by name, or a list of all symbol names if no name is provided.

Uses `SymbolService`.

### Query Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `symbol_name` | string | No | The name of a symbol. If provided, returns its corresponding ID; otherwise, a list of all symbol names is returned. |

### Response `200`

**With `symbol_name` provided:**
| Field Name | Type | Description |
|------|------ | -------------|
| `results` | integer | The ID for a symbol with a matching name.  |

&nbsp;

**Without `symbol_name`:**
| Field Name | Type | Description |
|------|------ | -------------|
| `results` | array (integer) | A list of all symbol names in the database.  |

### Examples

**With `symbol_name`:**

```
GET https://followthatfred.com/api/symbols?symbol_name=example1
```

```json
{
    "results": 1
}
```

**Without `symbol_name`:**

```
GET https://followthatfred.com/api/symbols
```

```json
{
    "results": ["example1", "example2", ...]
}
```



## POST `/symbols`
Creates a new symbol with the provided name.

Uses `SymbolService`.

### Body Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | Yes | The name of the new symbol. |


### Response `200`

| Field Name | Type | Description |
|------|------ | -------------|
| `id` | integer | The ID of the newly created symbol.  |

### Example

**Request:**

```
POST https://followthatfred.com/api/symbols
```

```json
{
    "name": "New Symbol"
}
```

**Response:**

```json
{
    "id": 5
}
```

## GET `/record_verifier`
Retrieves a paginated list of unverified records for a given record type.

Uses `RecordService`.

### Query Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `page` | int | Yes | The page corresponding to a collection of records to return. Currently, the number of records per page is 250.  |
| `type` | int | Yes | The type of train records to return. EOT: 1, HOT: 2, DPU: 3. Currently, DPU is not supported. |

### Response `200`


| Name | Type | Description |
|------|------ | -------------|
| `results` | array | An array containing up to 250 train records for the provided page.  |
| `type` | int | A number specifying the total number of pages available. |



### Examples

**Getting the first page of unverified EOT records:**

```
GET https://followthatfred.com/api/record_verifier?page=1&type=2
```

```json
{
    "results": [
        {
            "id": 1,
            "date_rec": "2025-03-25 05:20:00",
            "station_name": "Solvay",
            "symb_name": "R2D2",
            "unit_addr": "4697",
            "signal_strength": 85.0,
            "verified": false,
            "first_seen": "2025-03-25 05:15:00",
            "last_seen": "2025-03-25 05:20:00",
            "occurrence_count": "2",
            "duration": "0:05:00",
            "locomotive_num": "12AB",
            "brake_pressure": "81",
            "motion": "1",
            "marker_light": "0",
            "turbine": "1",
            "battery_cond": "Good",
            "battery_charge": "0.0",
            "arm_status": "Unarmed"
        }, ...
    ],
    "totalCount": 5
}
```

## POST `/record_verifier`
Verifies a train record by assigning a symbol and engine number. *Should be a PUT request, but last year's team used POST.*

Uses `RecordService`.

### Body Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `id` | integer | Yes | ID of the record to verify. Must be greater than 1. |
| `type` | integer | Yes | The type of the train record that is being verified. EOT: `1`, HOT: `2`, DPU: `3`. Currently, DPU is not supported. |
| `symbol` | integer | No | The ID of the symbol being assigned to a record. This column is not updated if a value is not provided, or the value is less than `1`. |
| `locomotive` | string | No | The locomotive number being assigned to a record. This column is not updated if a value is not provided. |



### Response `200`

Returns an empty JSON object on success.


### Example

**Request:**

```
GET https://followthatfred.com/api/record_verifier
```

```json
{
    "id": 1,
    "type": 1,
    "symbol": 2,
    "locomotive": "7475"
}
```

**Response:**

```json
{}
```

# User Endpoints


# Station Endpoints

Most of the endpoints relating to Stations were unused but have been kept in the repository if needed in the future. Only the used endpoints are documented here.

## GET `station_online`
Retrieves the time and/or date that the server received a ping notification from a station.

Uses `StationService`.

### Query Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `station_name` | string | Yes | The name of the station to receive the last seen date.  |

### Response `200`


| Name | Type | Description |
|------|------ | -------------|
| `last_seen` | string | A datetime string. If the date is within today, it is formatted as `HH:MM AM/PM`; otherwise, it is formatted as `MON DD, YYYY at HH:MM AM/PM`. |



### Examples

**Getting a Station Last Seen Today**

```
GET https://followthatfred.com/api/station_online?station_name=Solvay
```

```json
{
    "last_seen": "03:55 AM"
}
```

**Last Seen Longer Than a Day**
```json
{
    "last_seen": "03 25, 2026 at 03:55AM"
}
```

## POST `station_online`

Updates the time and date a station pinged the server. This endpoint serves as the point a station can ping the server.

Uses `StationService`.

### Body Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `station_id` | integer | Yes | The ID of the station sending the ping request. |

### Response `200`

| Name | Type | Description |
|------|------|-------------|
| `last_seen` | string | The time and/or date as a formatted datetime string added to the database. Same formatting rules as a `GET` request. |


### Example

**Request:**

```
GET https://followthatfred.com/api/station_online
```

```json
{
    "station_id": 1,
}
```

**Response:**

```json
{
    "last_seen": "03:55 AM"
}
```
***or***
```json
{
    "last_seen": "03 25, 2026 at 03:55AM"
}
```

# Train History Endpoints

These endpoints deal mostly with retrieving EOT and HOT records. The creation of these records lies in the stations receiving the radio data. The users then access the data stored in the database.

## GET `/history`
Returns a singular record depending on the signal type and ID provided.

Uses `RecordService`.

### Query Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `type` | integer | Yes | The type of the train record that is being verified. EOT: `1`, HOT: `2`, DPU: `3`. Currently, DPU is not supported. |
| `id` | integer | Yes | The ID of the record to retrieve. |

### Response Fields for EOT & HOT

| Name | Type | Description |
|------|------|-------------|
| `id` | integer | The ID of the record. |
| `date_rec` | integer | The date the record data was received by a station (or server). |
| `station_name` | integer | The ID of a station that the data was recorded at. |
| `symb_name` | string | The name of the symbol assigned to a record. |
| `unit_addr` | string | The unit address assigned to a record. This was never described to our team, but it might be the address of the unit sending the signal? |
| `verified` | boolean | Whether a record was verified by a Volunteer or Admin. |

***Specific Fields for EOT***

| Name | Type |
|------|------|
| `brake_pressure` | string |
| `motion` | string |
| `marker_light` | string |
| `turbine` | string |
| `batter_cond` | string |
| `battery_charge` | string |
| `arm_status` | string |
| `signal_strength` | string |

***Specific Fields for HOT***

| Name | Type |
|------|------|
| `frame_sync` | string |
| `command` | string |
| `checkbits` | string |
| `parity` | string |

### Example EOT

```
GET https://followthatfred.com/api/history?type=1&id=720000
```

```json
{
    "id": 720000,
    "date_rec": "2026-04-26 00:09:32",
    "station_name": "Silver Springs",
    "symbol_name": null,
    "unit_addr": "76315",
    "brake_pressure": "62",
    "motion": "0",
    "marker_light": "1",
    "turbine": "1",
    "battery_cond": "Good",
    "battery_charge": "0.0",
    "arm_status": "Unarmed",
    "signal_strength": 85.0,
    "verified": false
}
```

### Example HOT

```
GET https://followthatfred.com/api/history?type=2&id=20000
```

```json
{
    "id": 20000,
    "date_rec": "2025-06-28 18:41:41.947820",
    "station_name": "Fairport",
    "symbol_id": null,
    "unit_addr": "5354",
    "frame_sync": "unknown",
    "command": "Status request",
    "checkbits": "unknown",
    "parity": "unknown",
    "verified": false
}
```

## POST `/history`

Adds new record to the database. Additionally, handles logic for updating the map pins to know which signals are the most recently detected with that unit address. The notification system was broken when we received the project; however, the request should also determine whether input data warrants sending a notification, and then make the appropriate calls to notify users about the new train data.

Uses `RecordService`.

### Body Parameters for EOT & HOT

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `type` | integer | Yes | The type of record that is being created. EOT: `1`, HOT: `2`, DPU: `3`. Currently, DPU is not supported. |
| `date_rec` | string | No | The date and time the signal was received. This should be included if the station failed to create a record on the server. When excluded, the server assumes no recovery request was made after a failed creation attempt, and timestamps the record using the time the request arrived. |
| `station_id` | integer | Yes | The station ID where the signal data was recorded at. |
| `unit_addr` | string | No | The unit address assigned to a record. This was never described to our team, but it might be the address of the unit sending the signal? |
| `signal_strength` | float | No | Strength of the recorded signal. Default: 0.0 |

***Specific Fields for EOT***

| Name | Type | Required |
|------|------|----------|
| `brake_pressure` | string | No |
| `motion` | string | No |
| `marker_light` | string | No |
| `turbine` | string | No |
| `batter_cond` | string | No |
| `battery_charge` | string | No |
| `arm_status` | string | No |

***Specific Fields for HOT***

| Name | Type | Required |
|------|------|----------|
| `frame_sync` | string | No |
| `command` | string | No |
| `checkbits` | string | No |
| `parity` | string | No |


# Recent Activities Endpoint

# Record Collation Endpoint