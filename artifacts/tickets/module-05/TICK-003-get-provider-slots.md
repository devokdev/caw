# TICK-003: GET /api/providers/:id/slots — Fetch Available Provider Slots

## 1. Title
`TICK-003: GET /api/providers/:id/slots — Fetch Available Time Slots for Provider`

## 2. Context (Why)
After selecting a provider from the catalog, a consumer needs to view the provider's available schedule to pick a booking time.

## 3. Scope (What)
Implement `GET /api/providers/:id/slots` returning all unbooked time slots (`status = 'AVAILABLE'`) associated with the specified provider UUID.

## 4. Interface Contract
- **Method / Route:** `GET /api/providers/:id/slots`
- **URL Parameters:**
  - `id`: UUID (Provider ID)
- **Success Response (200 OK):**
  ```json
  {
    "provider_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    "slots": [
      {
        "slot_id": "b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22",
        "start_time": "2026-08-20T14:00:00Z",
        "end_time": "2026-08-20T15:00:00Z",
        "status": "AVAILABLE"
      }
    ]
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: If `:id` is not a valid UUID (`{ "error": "Invalid provider UUID" }`).
  - `404 Not Found`: If provider does not exist (`{ "error": "Provider not found" }`).

## 5. Acceptance Criteria (Given/When/Then)
- **AC-1:** Given a valid provider with 3 open slots, When sending `GET /api/providers/:id/slots`, Then return HTTP 200 with an array containing the 3 available slots.
- **AC-2:** Given a slot has already been booked (`status = 'BOOKED'`), When calling `GET /api/providers/:id/slots`, Then the booked slot is filtered out of the response.
- **AC-3:** Given a non-existent provider UUID, When calling this endpoint, Then return HTTP 404 with error message `"Provider not found"`.

## 6. Constraints
- Slots must be returned sorted chronologically by `start_time` ascending.
- Must validate UUID format before running database query.

## 7. Anti-Scope
- No timezone conversion on backend (all timestamps returned as ISO 8601 UTC).
- No recurring slot expansion logic.
- No temporary holding lock mechanism (handled in Slice 4).
