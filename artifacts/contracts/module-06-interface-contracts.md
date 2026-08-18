# Module 06: Interface Contracts Specification

## Contract: Provider Availability API <-> Booking Creation API

### Shared Identifiers & Types
- `provider_id`: UUIDv4 string (e.g. `usr_99a8b7c6d5e4f3a2`)
- `slot_id`: UUIDv4 string (e.g. `slt_aabbccddeeff0011`)
- `user_id`: UUIDv4 string (e.g. `usr_c1234567890abcdef`)
- `datetime`: ISO 8601 UTC timestamp string (e.g. `2026-09-01T10:00:00.000Z`)

---

### Stream 1: Provider Availability API (TICKET-03)
- **Method & Route**: `GET /api/v1/providers/:provider_id/slots?date=YYYY-MM-DD`
- **Response 200 OK**:
```json
{
  "provider_id": "usr_99a8b7c6d5e4f3a2",
  "date": "2026-09-01",
  "slots": [
    {
      "slot_id": "slt_aabbccddeeff0011",
      "start_time": "2026-09-01T10:00:00.000Z",
      "end_time": "2026-09-01T11:00:00.000Z",
      "status": "available"
    }
  ]
}
```
- **Error Responses**:
  - `400 Bad Request`: `{"error": "invalid_date_format"}`
  - `404 Not Found`: `{"error": "provider_not_found"}`

---

### Stream 2: Booking Creation API (TICKET-04)
- **Method & Route**: `POST /api/v1/bookings`
- **Request Headers**:
  - `Authorization: Bearer <jwt_token>`
  - `Idempotency-Key: <uuid_v4>`
- **Request Body**:
```json
{
  "provider_id": "usr_99a8b7c6d5e4f3a2",
  "slot_id": "slt_aabbccddeeff0011",
  "service_id": "srv_1122334455667788",
  "customer_notes": "Focus on shoulder mobility"
}
```
- **Response 201 Created**:
```json
{
  "booking_id": "bok_445566778899aabb",
  "provider_id": "usr_99a8b7c6d5e4f3a2",
  "slot_id": "slt_aabbccddeeff0011",
  "customer_id": "usr_c1234567890abcdef",
  "status": "pending_confirmation",
  "total_amount_cents": 7500,
  "currency": "USD",
  "booked_at": "2026-08-19T02:00:00.000Z"
}
```
- **Error Responses**:
  - `400 Bad Request`: `{"error": "missing_required_fields"}`
  - `401 Unauthorized`: `{"error": "unauthorized"}`
  - `409 Conflict`: `{"error": "slot_already_booked"}`

---

### Synchronization Point Contract
- When Booking API claims a slot, it executes `PATCH /api/v1/slots/:slot_id` with `{"status": "locked", "held_by_booking_id": "bok_445566778899aabb"}` within a database transaction to prevent race conditions.
