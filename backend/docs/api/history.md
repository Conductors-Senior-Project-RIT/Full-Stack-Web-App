# Train History Endpoints

These endpoints deal mostly with retrieving and creating EOT and HOT records. The creation of these records lies in the stations receiving the radio data. The users then access the data stored in the database.

## GET `/history`

Returns a singular record depending on the signal type and ID provided.

Uses [`RecordService`][src.service.record_service.RecordService].

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

Uses [`RecordService`][src.service.record_service.RecordService].

### Body Parameters for EOT & HOT

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `type` | integer | Yes | The type of record that is being created. EOT: `1`, HOT: `2`, DPU: `3`. Currently, DPU is not supported. |
| `date_rec` | string | No | The date and time the signal was received. This should be included if the station failed to create a record on the server. When excluded, the server assumes no recovery request was made after a failed creation attempt, and timestamps the record using the time the request arrived. Format: `%Y-%m-%d %H:%M:%S` |
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

### Example EOT

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

### Example HOT

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
