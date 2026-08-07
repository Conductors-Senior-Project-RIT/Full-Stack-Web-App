# Station Endpoints

Most of the endpoints relating to Stations were unused but have been kept in the repository if needed in the future. Only the used endpoints are documented here.

## GET `/station_online`

Retrieves the time and/or date that the server received a ping notification from a station.

Uses [`StationService`][src.service.station_service.StationService].

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

Uses [`StationService`][src.service.station_service.StationService].

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