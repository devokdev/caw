# TICK-004: POST /api/bookings — Create Confirmed Booking (AI-Ready Spec)

## 1. Title
`TICK-004: POST /api/bookings — Create Confirmed Booking`

## 2. Context (Why)
This represents the primary transaction endpoint in the marketplace. When a user selects an available time slot and clicks "Confirm Booking", this endpoint validates availability, marks the slot as booked, persists the booking record, and returns a verified booking confirmation.

## 3. Scope (What)
Create a single HTTP POST endpoint at `/api/bookings` in `src/modules/bookings/bookings.router.ts` and `bookings.service.ts` that executes an atomic database transaction to book a slot.

## 4. Interface Contract
- **Method / Route:** `POST /api/bookings`
- **Request Headers:**
  - `Content-Type: application/json`
- **Request Body (JSON):**
  ```json
  {
    "provider_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    "slot_id": "b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22",
    "customer_name": "Jane Doe",
    "customer_email": "jane@example.com",
    "notes": "Interested in beginner lessons"
  }
  ```
- **Success Response (201 Created):**
  ```json
  {
    "booking_id": "c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a33",
    "status": "CONFIRMED",
    "provider_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    "slot_id": "b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22",
    "customer_name": "Jane Doe",
    "customer_email": "jane@example.com",
    "created_at": "2026-08-20T12:00:00.000Z"
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: If `provider_id`, `slot_id`, `customer_name`, or `customer_email` is missing or invalid.
    ```json
    { "error": "Validation error: customer_email is required and must be a valid email" }
    ```
  - `404 Not Found`: If `provider_id` or `slot_id` does not exist.
    ```json
    { "error": "Provider or slot not found" }
    ```
  - `409 Conflict`: If `slot_id` has already been booked (`status != 'AVAILABLE'`).
    ```json
    { "error": "Slot already booked" }
    ```

## 5. Acceptance Criteria (Given/When/Then)
- **AC-1:** Given a valid available slot, When sending `POST /api/bookings` with valid JSON payload, Then return HTTP 201 with booking object and set slot status to `BOOKED` in the database.
- **AC-2:** Given a missing required field (e.g. `customer_email`), When `POST /api/bookings` is submitted, Then return HTTP 400 with a descriptive validation error message.
- **AC-3:** Given a slot ID that is already marked `BOOKED`, When `POST /api/bookings` is called for that slot, Then return HTTP 409 Conflict with `{ "error": "Slot already booked" }` and do not create a duplicate booking.
- **AC-4:** Given a non-existent provider ID or slot ID, When `POST /api/bookings` is called, Then return HTTP 404 with `{ "error": "Provider or slot not found" }`.

## 6. Constraints
- Use database transaction (`BEGIN ... COMMIT`) to ensure atomicity between slot update and booking insert.
- Generate standard UUID v4 for `booking_id`.
- Adhere strictly to the project's centralized error handling middleware in `src/middleware/error.handler.ts`.

## 7. Anti-Scope
- No Stripe credit card charge or payment gateway verification (separate payment ticket).
- No SMTP/SES email delivery (confirmation returned directly in HTTP response).
- No SMS or Webhook notifications.
- No user authentication tokens / sessions required in Slice 1.
