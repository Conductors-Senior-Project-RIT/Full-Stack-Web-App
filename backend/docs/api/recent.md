# Recent Activities Endpoint

## GET `/recent_activities`

Returns records at a provided station within a specified timeframe. The specified time range serves as a lower bound, while the time the request was received serves as an upper bound.

Uses [`RecordService`][src.service.record_service.RecordService].

### Query Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `type` | integer | No | The type of the records that are being retrieved. EOT: 1, HOT: 2, DPU: 3. Currently, DPU is not supported. If no type is provided, records of all types are returned. |
| `station_id` | integer | No | The ID associated with a station used to retrieve the records it has recorded. If this field is not provided, `station_name` must be provided as a parameter. |
| `timerange` | string | No | Delta time that defines the range records should be pulled from. Format: `HH:MM:SS`. Default: `12:00:00`. |
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
