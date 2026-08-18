# TICK-005: POST /api/providers — Provider Self-Registration (AI-Ready Spec)

## 1. Title
`TICK-005: POST /api/providers — Provider Self-Registration`

## 2. Context (Why)
In Slice 2 (Provider Onboarding), service providers need a self-service registration endpoint to create their initial profile. The profile begins in `DRAFT` status and must transition through vetting before appearing in marketplace search.

## 3. Scope (What)
Implement `POST /api/providers` to ingest provider registration details, validate mandatory profile fields, create a provider record in PostgreSQL with `status = 'DRAFT'`, and return the created provider object.

## 4. Interface Contract
- **Method / Route:** `POST /api/providers`
- **Request Headers:**
  - `Content-Type: application/json`
- **Request Body (JSON):**
  ```json
  {
    "name": "David Drum Lessons",
    "email": "david@example.com",
    "category": "MUSIC",
    "city": "Austin",
    "hourly_rate_cents": 6000,
    "bio": "Professional touring drummer with 10 years of teaching experience."
  }
  ```
- **Success Response (201 Created):**
  ```json
  {
    "id": "d3eebc99-9c0b-4ef8-bb6d-6bb9bd380a44",
    "name": "David Drum Lessons",
    "email": "david@example.com",
    "category": "MUSIC",
    "city": "Austin",
    "hourly_rate_cents": 6000,
    "rating": 0.0,
    "status": "DRAFT",
    "created_at": "2026-08-20T12:00:00.000Z"
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: If `hourly_rate_cents <= 0`, email is invalid, or required fields are missing.
    ```json
    { "error": "Validation error: hourly_rate_cents must be a positive integer" }
    ```
  - `409 Conflict`: If `email` already exists in `providers` table.
    ```json
    { "error": "Email already registered" }
    ```

## 5. Acceptance Criteria (Given/When/Then)
- **AC-1:** Given valid provider profile payload, When calling `POST /api/providers`, Then create a record in `providers` table with status `DRAFT` and return HTTP 201.
- **AC-2:** Given a registered email address, When calling `POST /api/providers` with the same email, Then return HTTP 409 Conflict with `"Email already registered"`.
- **AC-3:** Given `hourly_rate_cents` is negative or non-numeric, When submitting `POST /api/providers`, Then return HTTP 400 Bad Request.
- **AC-4:** Given a new provider is created in `DRAFT` status, When querying `GET /api/providers`, Then this provider is not returned in public search results.

## 6. Constraints
- Normalize `city` string to capitalized title case (e.g., "Austin").
- Store all monetary values as integer cents (`hourly_rate_cents`).
- Enforce unique constraint on `providers.email` in database.

## 7. Anti-Scope
- No document upload or background check verification logic.
- No automated transition to `APPROVED` (admin review is separate ticket).
- No Stripe Express account linking.
