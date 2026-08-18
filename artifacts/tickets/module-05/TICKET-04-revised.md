# Module 05: Task Specification - Fixed Ticket 04 (Booking Creation API)

## Ticket Overview
- **Ticket ID**: TICKET-04
- **Title**: Implement Booking Creation API Endpoint (`POST /api/v1/bookings`)
- **Assignee**: Backend Engineer / Agent 04
- **Dependencies**: TICKET-01 (Database Schema), TICKET-02 (Auth & RBAC Middleware)

---

## 1. Context & Scope
Provide a secure, validated, and idempotent REST API endpoint for customers to create appointments with providers.

---

## 2. API Contract Specification

### Request Interface
- **Method & Path**: `POST /api/v1/bookings`
- **Headers**:
  - `Authorization: Bearer <jwt_token>` (Required)
  - `Idempotency-Key: <uuid_v4>` (Required)
  - `Content-Type: application/json` (Required)
- **Request Body**:
```json
{
  "provider_id": "usr_99a8b7c6d5e4f3a2",
  "service_id": "srv_1122334455667788",
  "start_time": "2026-09-01T10:00:00.000Z",
  "end_time": "2026-09-01T11:00:00.000Z",
  "customer_notes": "First time consultation. Focus on lower back stiffness."
}
```

### Validation & Security Rules
1. **Authentication & Authorization**:
   - Extract `customer_id` strictly from verified JWT claims (`req.user.id`). Reject unauthenticated requests with `401 Unauthorized`.
   - Ensure `req.user.role == 'customer'`. Reject forbidden roles with `403 Forbidden`.
2. **Input Sanitization**:
   - `customer_notes` max 1000 characters. Strip all HTML/script tags to prevent XSS.
3. **Temporal Validity**:
   - `start_time` must be in the future (minimum +30 minutes from `now()`).
   - `end_time` must equal `start_time + service.duration_minutes`.
4. **Provider Availability & Concurrency Guard**:
   - Use `SELECT ... FOR UPDATE` or database advisory locks to guarantee no overlapping active bookings for `provider_id`.
5. **Idempotency**:
   - Cache `(Idempotency-Key, customer_id)` responses in Redis with 24-hour TTL to return cached output on client retries without double-charging or duplicate bookings.

---

## 3. Response Contracts & Status Codes

- **201 Created**: Booking created successfully.
```json
{
  "booking_id": "bok_445566778899aabb",
  "status": "pending_confirmation",
  "customer_id": "usr_c1234567890abcdef",
  "provider_id": "usr_99a8b7c6d5e4f3a2",
  "service_id": "srv_1122334455667788",
  "start_time": "2026-09-01T10:00:00.000Z",
  "end_time": "2026-09-01T11:00:00.000Z",
  "total_amount_cents": 8500,
  "currency": "USD",
  "created_at": "2026-08-19T01:58:00.000Z"
}
```
- **400 Bad Request**: Missing required fields or schema violation.
- **401 Unauthorized**: Missing/invalid bearer token.
- **403 Forbidden**: Caller lacks customer role.
- **409 Conflict**: Provider already booked for requested time window.
- **500 Internal Server Error**: Uncaught downstream exception with error correlation ID.

---

## 4. Anti-Scope
- No direct credit card capture or payment gateway invocation in this ticket (handled asynchronously in TICKET-05 via payment intent webhook).
- No provider email/SMS notifications (handled by event subscriber in TICKET-06).
