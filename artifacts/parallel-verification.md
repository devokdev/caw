# Module 06: Verification Walkthrough - Sarah Booking Mike Scenario

## End-to-End Traceability Verification

1. **Step 1: Slot Browsing & Discovery**:
   - **Stream**: Agent 01 (Availability API - TICKET-03).
   - **Request**: `GET /api/v1/providers/usr_99a8b7c6d5e4f3a2/slots?date=2026-09-01`
   - **Response Output**:
     ```json
     {
       "provider_id": "usr_99a8b7c6d5e4f3a2",
       "date": "2026-09-01",
       "slots": [
         {
           "slot_id": "slt_aabbccddeeff0011",
           "start_time": "2026-09-01T14:00:00.000Z",
           "end_time": "2026-09-01T15:00:00.000Z",
           "status": "available"
         }
       ]
     }
     ```

2. **Step 2: Booking Submission**:
   - **Stream**: Agent 02 (Booking Creation API - TICKET-04).
   - **Request**: `POST /api/v1/bookings` with payload:
     ```json
     {
       "provider_id": "usr_99a8b7c6d5e4f3a2",
       "slot_id": "slt_aabbccddeeff0011",
       "service_id": "srv_plumbing_std",
       "customer_notes": "Plumbing leak under sink"
     }
     ```
   - **Type Compatibility**: `provider_id` and `slot_id` conform exactly to UUID string types across both agent boundaries.

3. **Step 3: Concurrency Race Condition Handling**:
   - If slot `slt_aabbccddeeff0011` is claimed concurrently, Agent 02's advisory lock triggers a conflict check and returns `409 Conflict: {"error": "slot_already_booked"}` as specified in the interface contract.
