# Module 08: Integration Test Plan

## Suite Overview: Cross-Component Integration Gates

### Test 1: Happy Path Booking with Notification Dispatch
- **Components Involved**: Provider Catalog, Booking API, Notification Service
- **Precondition**: Provider with active available slot `SLOT-101` in database.
- **Steps**:
  1. Consumer queries `GET /api/v1/providers/P-01/slots`.
  2. Consumer submits `POST /api/v1/bookings` with `slot_id: "SLOT-101"`.
  3. Verify HTTP 201 response with `status: "confirmed"`.
  4. Verify Notification Service receives event with matching ISO-8601 UTC `created_at`.
- **Contract Points Validated**: Booking creation contract and event emission contract.

---

### Test 2: Double-Booking Concurrency Conflict Handling
- **Components Involved**: Booking API, Postgres Database Transaction Lock
- **Precondition**: Single available slot `SLOT-202`.
- **Steps**:
  1. Two concurrent requests issue `POST /api/v1/bookings` for `SLOT-202`.
  2. Request A completes with HTTP 201 Created.
  3. Request B receives HTTP 409 Conflict with code `SLOT_ALREADY_BOOKED`.
- **Contract Points Validated**: Idempotency and database row-level locking.

---

### Test 3: Corporate Manager Delegation Authorization Gate
- **Components Involved**: Auth Middleware, Booking API, RBAC Policy Engine
- **Precondition**: Manager user `MGR-01` and Employee user `EMP-02` in same `ORG-99`.
- **Steps**:
  1. `MGR-01` issues `POST /api/v1/bookings` with `booked_for_user_id: EMP-02.id`.
  2. Verify HTTP 201 Created with booking record associated to `EMP-02`.
  3. `EMP-02` issues `POST /api/v1/bookings` with `booked_for_user_id: MGR-01.id`.
  4. Verify HTTP 403 Forbidden (`INSUFFICIENT_ROLE_PERMISSIONS`).
- **Contract Points Validated**: Multi-tenant claims authorization contract.
