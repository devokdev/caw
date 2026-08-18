# Module 08: Integration & Pre-Merge Checklist

## Phase 1: Pre-Integration Contract Audit

| Contract Boundary | Service A (Producer) | Service B (Consumer) | Verification Result | Fix / Mitigation |
|---|---|---|---|---|
| Slot Availability -> Booking Creation | `slot_id`: UUID, `status`: "available" | `slot_id`: UUID, `status`: "available" | PASSED | Consistent UUID v4 and lowercase enum string. |
| Booking Creation -> Provider Notification | `created_at`: ISO-8601 UTC string | `created_at`: ISO-8601 UTC string | PASSED | Resolved integer timestamp drift by standardizing on ISO-8601 UTC across all event payloads. |
| Booking Delegation -> User Identity | `booked_for_user_id`: UUID | `user_id`: UUID | PASSED | Enforces same-org authorization checks before booking creation. |

---

## Phase 2: Incremental Merge Log

1. **Merge Step 1: Auth & User Identity Service (TICKET-01, TICKET-07)**
   - *Status*: Merged cleanly. JWT claims include `org_id` and `role`.
2. **Merge Step 2: Provider Catalog & Availability Service (TICKET-02, TICKET-03)**
   - *Status*: Merged cleanly. Slot queries respect real-time availability filters.
3. **Merge Step 3: Booking & Notification Service (TICKET-04, TICKET-05)**
   - *Status*: Merged cleanly. Verified delegate booking persistence and notification dispatch.
