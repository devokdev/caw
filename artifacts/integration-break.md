# Module 08: Integration Bug Root Cause Analysis & Seam Diagnosis

## 1. Symptom & Evidence
- **Symptom**: Newly created bookings do not appear on the Provider Dashboard.
- **Provider Dashboard Query**: Queries bookings with `status = 'active'`.
- **Booking Creation Mutation**: Persists new bookings with `status = 'confirmed'`.

---

## 2. Root Cause Analysis
This is **not a code bug** inside either component:
- The Booking Service is 100% compliant with its internal specification (`status: "confirmed"` indicates a valid, completed booking).
- The Provider Dashboard is 100% compliant with its internal specification (`status: "active"` indicates currently active jobs for display).

The bug lives entirely in the **space between them** (an interface semantic contract mismatch). Neither service shared an explicit enum definition of booking lifecycle states.

---

## 3. Immediate Architectural Fix
1. **Define Shared Booking Lifecycle State Machine**:
   - `confirmed`: Booking reserved and valid.
   - `in_progress`: Session currently ongoing.
   - `completed`: Session finished.
   - `cancelled`: Session voided / refunded.
2. **Update Provider Dashboard Filter**:
   - Modify Provider Dashboard query filter to include all non-terminal states: `WHERE status IN ('confirmed', 'in_progress')`.
3. **Add Automated Cross-Component Contract Test**:
   - Integration test that creates a booking via API and asserts visibility in dashboard endpoint response.
