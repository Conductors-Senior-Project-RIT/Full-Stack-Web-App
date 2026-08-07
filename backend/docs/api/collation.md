# Record Collation Endpoint

## GET `/record_collation`

Retrieves a paginated collation of train records grouped by unit address and station. Groups are formed when either the station changes or a duration of more than 2 hours elapses between records. Returns the most recent record per group along with aggregate information such as `first_seen`, `last_seen`, `occurrence_count`, and `duration`.

Uses [`RecordService`][src.service.record_service.RecordService].

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
