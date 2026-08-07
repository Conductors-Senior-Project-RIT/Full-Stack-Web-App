# Volunteer Endpoints

These endpoints can only be accessed by users with *Volunteer* or *Admin* permissions. The `role_required` decorator in [`api_core.decorators`](./core/decorators.md) can be applied to a Flask route to restrict access to authorized users only.

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

Uses [`SymbolService`][src.service.symbol_service.SymbolService].

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

Uses [`SymbolService`][src.service.symbol_service.SymbolService].

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

Uses [`RecordService`][src.service.record_service.RecordService].

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

## PUT `/record_verifier`

Verifies a train record by assigning a symbol and locomotive number.

Uses [`RecordService`][src.service.record_service.RecordService].

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
