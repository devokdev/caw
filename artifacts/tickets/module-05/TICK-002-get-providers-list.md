# TICK-002: GET /api/providers — List Marketplace Providers

## 1. Title
`TICK-002: GET /api/providers — List Approved Providers with Summary Info`

## 2. Context (Why)
Consumers visiting the homepage need to browse active providers. This endpoint provides the marketplace catalog view for the frontend discovery UI.

## 3. Scope (What)
Create an Express route `GET /api/providers` that queries the database for all providers where `status = 'APPROVED'` and returns a JSON list sorted by rating descending.

## 4. Interface Contract
- **Method / Route:** `GET /api/providers`
- **Query Params:**
  - `category` (optional, string): Filters providers by exact category match (e.g. `?category=TECH`).
- **Success Response (200 OK):**
  ```json
  [
    {
      "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
      "name": "Bob Python Mentoring",
      "category": "TECH",
      "hourly_rate_cents": 5000,
      "rating": 5.0,
      "bio": "Senior full-stack engineer offering 1-on-1 architecture & coding mentorship."
    }
  ]
  ```
- **Error Responses:**
  - `500 Internal Server Error`: `{ "error": "Internal database error" }`

## 5. Acceptance Criteria (Given/When/Then)
- **AC-1:** Given approved providers exist in the database, When a client sends `GET /api/providers`, Then the server returns HTTP 200 with an array of approved provider objects.
- **AC-2:** Given unapproved/draft providers exist, When `GET /api/providers` is called, Then unapproved providers are excluded from the response.
- **AC-3:** Given a query param `?category=MUSIC`, When `GET /api/providers?category=MUSIC` is called, Then only providers in the `MUSIC` category are returned.

## 6. Constraints
- Response latency must be < 50ms for local queries.
- Follow Express controller-service-repository pattern in `src/modules/providers/`.
- Return proper `Content-Type: application/json`.

## 7. Anti-Scope
- No pagination parameters (dataset is small seed list).
- No fuzzy text search or geographical distance calculation.
- No authentication requirements (public endpoint).
