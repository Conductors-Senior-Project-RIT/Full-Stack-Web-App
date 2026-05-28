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
            "date_rec": "2026-03-25 05:20:00",
            "station_name": "Solvay",
            "symb_name": "R2D2",
            "unit_addr": "4697",
            "signal_strength": 85.0,
            "verified": false,
            "first_seen": "2026-03-25 05:15:00",
            "last_seen": "2026-03-25 05:20:00",
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

## GET `/station_online`
Retrieves the time and/or date that the server received a ping notification from a station.

Uses `StationService`.

### Query Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `station_name` | string | Yes | The name of the station to retrieve the last seen date and time for.  |

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

## POST `/station_online`

Updates the time and date a station pinged the server. This endpoint serves as the point a station can ping the server. Should be a PUT
request, but last year's team used a POST.

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
| `type` | integer | Yes | The type of the train record that is being retrieved. EOT: `1`, HOT: `2`, DPU: `3`. Currently, DPU is not supported. |
| `id` | integer | Yes | The ID of the record to retrieve. |

### Response Fields for EOT & HOT

| Name | Type | Description |
|------|------|-------------|
| `id` | integer | The ID of the record. |
| `date_rec` | string | The date the record data was received by a station (or server). |
| `station_name` | integer | The ID of a station that the data was recorded at. |
| `symb_name` | string | The name of the symbol assigned to a record. |
| `unit_addr` | string | The unit address assigned to a record. This was never described to our team, but it might be the address of the unit sending the signal? |
| `verified` | boolean | Whether a record was verified by a Volunteer or Admin. |

&nbsp;

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

&nbsp;

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
    "date_rec": "2026-06-28 18:41:41.947820",
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
| `date_rec` | string | No | The date and time the signal was received. This should be included if the station failed to create a record on the server. When excluded, the server assumes no recovery request was made after a failed creation attempt, and timestamps the record using the time the request arrived. Format: `%Y-%m-%d %H:%M:%S` |
| `station_id` | integer | Yes | The station ID where the signal data was recorded at. |
| `unit_addr` | string | No | The unit address assigned to a record. This was never described to our team, but it might be the address of the unit sending the signal? |
| `signal_strength` | float | No | Strength of the recorded signal. Default: 0.0 |

&nbsp;

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

&nbsp;

***Specific Fields for HOT***

| Name | Type | Required |
|------|------|----------|
| `frame_sync` | string | No |
| `command` | string | No |
| `checkbits` | string | No |
| `parity` | string | No |

### Example EOT:

```
POST https://followthatfred.com/api/history
```

```json
{
    "type": 1,
    "date_rec": "2026-03-25 03:55:55",
    "station_id": 1,
    "unit_addr": "5544",
    "signal_strength": 80.0,
    "brake_pressure": "62",
    "motion": "0",
    "marker_light": "1",
    "turbine": "1",
    "battery_cond": "Good",
    "battery_charge": "0.0",
    "arm_status": "Unarmed"
}
```

### Example HOT:
```json
{
    "type": 2,
    "date_rec": "2026-03-28 18:41:41",
    "station_id": 2,
    "unit_addr": "5354",
    "signal_strength": 60.0,
    "frame_sync": "something",
    "command": "Status request",
    "checkbits": "something",
    "parity": "something"
}
```

# Recent Activities Endpoint

## GET `/recent_activities`
Returns records at a provided station within a specified timeframe. The specified time range serves as a lower bound, while the time the request was received serves as an upper bound.

Uses `RecordService`.

### Query Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `type` | integer | No | The type of the records that are being retrieved. EOT: 1, HOT: 2, DPU: 3. Currently, DPU is not supported. If no type is provided, records of all types are returned. |
| `station_id` | integer | No | The ID associated with a station used to retrieve the records it has recorded. If this field is not provided, `station_name` must be provided as a parameter. |
| `timerange` | string | Yes | Delta time that defines the range records should be pulled from. Format: `HH:MM:SS` |
| `most_recent` | boolean | No | A boolean that determines if the most recent records should be retrieved (where `most_recent` is True in database). Default: True |
| `station_name` | string | No | If `station_id` is not provided, the name of the station can be used to retrieve records; however, in that case, this field is required. |


### Response `200`

Returns a sorted array of train records by the date they were received in descending order. The array will contain records of every type, with a record's type denoted by the `Data_type` field, which includes the possible values: `EOT`, `HOT`. `DPU` will be included in future iterations.

***Fields***

| Name | Type |
|------|------|
| `id` | integer |
| `date_rec` | string |
| `station_name` | string |
| `symb_name` | string | 
| `unit_addr` | string |
| `engine_num` | int |
| `locomotive_num` | string |


### Example

```
GET https://followthatfred.com/api/recent_activities?station_name=Macedon&timerange=12:00:00
```

```json
[
    {
        "id": 1738, 
        "unit_addr": "4140", 
        "date_rec": "2026-03-23 15:06:20", 
        "station_name": "Macedon", 
        "symb_name": null, 
        "engine_num": null, 
        "locomotive_num": "unknown", 
        "Data_type": "EOT"
    }, 
    {
        "id": 2399, 
        "unit_addr": "4140", 
        "date_rec": "2026-03-22 15:05:52", 
        "station_name": "Macedon",
        "symb_name": null,
        "engine_num": null,
        "locomotive_num": "unknown", 
        "Data_type": "HOT"
    }
]
```

# Record Collation Endpoint

## GET `/record_collation`

Retrieves a paginated collation of train records grouped by unit address and station. Groups are formed when either the station changes or a duration of more than 2 hours elapses between records. Returns the most recent record per group along with aggregate information such as `first_seen`, `last_seen`, `occurrence_count`, and `duration`.

Uses `RecordService`.

### Query Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `type` | integer | No | The type of the records that are being retrieved. EOT: 1, HOT: 2, DPU: 3. Currently, DPU is not supported. Default: 1 |
| `page` | integer | No | The page corresponding to a collection of records to return. Currently, the number of records per page is 250. Must be greater than 1. Default: 1 |


### Response Fields

| Name | Type | Description |
|------|------|-------------|
| `results` | array | An array containing the retrieved records for a page. |
| `totalPages` | integer | The total number of pages that can be accessed. |

&nbsp;

***Results Fields for EOT & HOT***

| Name | Type |
|------|------|
| `id` | integer |
| `date_rec` | string |
| `station_name` | string |
| `symb_name` | string |
| `unit_addr` | string |
| `signal_strength` | float |
| `verified` | boolean |
| `first_seen` | string |
| `last_seen` | string |
| `occurrence_count` | integer |
| `duration` | string |
| `locomotive_num` | string |

&nbsp;

***Specific Fields for EOT***
| Name | Type |
|------|------|
| `brake_pressure` | string |
| `motion` | string |
| `marker_light` | string |
| `turbine` | string |
| `battery_cond` | string |
| `battery_charge` | string |
| `arm_status` | string |

&nbsp;

***Specific Fields for HOT***
| Name | Type |
|------|------|
| `frame_sync` | string |
| `command` | string |
| `checkbits` | string |
| `parity` | string |


### Example EOT

```
GET https://followthatfred.com/api/record_collation?type=1&page=1
```

```json
{
    "results": [
        {
            "id": 1,
            "date_rec": "2026-03-23 15:06:20",
            "station_name": "Pittsford",
            "symbol_id": null,
            "unit_addr": "54685",
            "brake_pressure": "84",
            "motion": "1",
            "marker_light": "0",
            "turbine": "1",
            "battery_cond": "Good",
            "battery_charge": "0.0",
            "arm_status": "Unarmed",
            "signal_strength": 85,
            "verified": false,
            "first_seen": "2026-03-23 15:05:38",
            "last_seen": "2026-03-23 15:06:20",
            "ocurrence_count": "3",
            "duration": "0:00:42",
            "symbol_name": null,
            "locomotive_num": "unknown"
        },
        {
            "id": 2,
            "date_rec": "2026-03-22 15:05:52",
            "station_name": "Macedon",
            "symbol_id": null,
            "unit_addr": "4140",
            "brake_pressure": "88",
            "motion": "1",
            "marker_light": "0",
            "turbine": "1",
            "battery_cond": "Good",
            "battery_charge": "0.0",
            "arm_status": "Unarmed",
            "signal_strength": 94,
            "verified": false,
            "first_seen": "2026-03-22 15:05:51",
            "last_seen": "2026-03-22 15:05:52",
            "ocurrence_count": "2",
            "duration": "0:00:01",
            "symbol_name": null,
            "locomotive_num": "unknown"
        }, ...
    ],
    "totalPages": 183
}
```

### Example HOT

```
GET https://followthatfred.com/api/record_collation?type=2&page=1
```

```json
{
    "results": [
        {
            "id": 1,
            "date_rec": "2026-03-27 15:31:27",
            "station_name": "Fairport",
            "symbol_id": null,
            "unit_addr": "54685",
            "signal_strength": 0,
            "verified": false,
            "locomotive_num": "unknown",
            "first_seen": "2026-03-27 15:27:26",
            "last_seen": "2026-03-27 15:31:27",
            "occurrence_count": "2",
            "duration": "0:04:01",
            "symbol_name": null,
            "command": "Status request"
        },
        {
            "id": 2,
            "date_rec": "2026-03-27 15:05:52",
            "station_name": "Macedon",
            "symbol_id": null,
            "unit_addr": "4140",
            "signal_strength": 0,
            "verified": false,
            "locomotive_num": "unknown",
            "first_seen": "2026-03-27 15:01:51",
            "last_seen": "2026-03-27 15:05:52",
            "occurrence_count": "3",
            "duration": "0:04:01",
            "symbol_name": null,
            "command": "Status request"
        }, ...
    ],
    "totalPages": 153
}
```
