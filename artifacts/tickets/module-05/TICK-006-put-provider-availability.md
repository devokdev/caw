# TICK-006: PUT /api/providers/:id/availability — Set Availability Schedule

## 1. Title
`TICK-006: PUT /api/providers/:id/availability — Set Provider Availability Schedule`

## 2. Context (Why)
Registered providers need to configure when they are available for bookings so that the marketplace can generate bookable slots for clients.

## 3. Scope (What)
Implement `PUT /api/providers/:id/availability` to replace or set a provider's availability slots for upcoming days.

## 4. Interface Contract
- **Method / Route:** `PUT /api/providers/:id/availability`
- **URL Parameters:**
  - `id`: UUID (Provider ID)
- **Request Body (JSON):**
  ```json
  {
    "slots": [
      {
        "start_time": "2026-08-21T09:00:00Z",
        "end_time": "2026-08-21T10:00:00Z"
      },
      {
        "start_time": "2026-08-21T11:00:00Z",
        "end_time": "2026-08-21T12:00:00Z"
      }
    ]
  }
  ```
- **Success Response (200 OK):**
  ```json
  {
    "provider_id": "d3eebc99-9c0b-4ef8-bb6d-6bb9bd380a44",
    "slots_created": 2,
    "status": "UPDATED"
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: If slot ranges overlap or `start_time >= end_time`.
    ```json
    { "error": "Validation error: start_time must be before end_time" }
    ```
  - `404 Not Found`: If provider does not exist.
    ```json
    { "error": "Provider not found" }
    ```

## 5. Acceptance Criteria (Given/When/Then)
- **AC-1:** Given a registered provider, When submitting a list of non-overlapping slots, Then create corresponding records in `availability_slots` with `status = 'AVAILABLE'` and return HTTP 200.
- **AC-2:** Given a slot where `start_time` is in the past, When submitting `PUT /api/providers/:id/availability`, Then return HTTP 400 Bad Request.
- **AC-3:** Given overlapping time intervals in the slot array, When submitting the request, Then return HTTP 400 with an overlap error.

## 6. Constraints
- Slots must be minimum 30 minutes and maximum 4 hours duration.
- Atomic transaction execution.

## 7. Anti-Scope
- No recurring weekly rule engine (explicit datetime slots only).
- No Google Calendar or iCal two-way synchronization.
- No auto-cancellation of conflicting existing bookings.
