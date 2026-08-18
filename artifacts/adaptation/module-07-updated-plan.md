# Module 07: Updated Execution Plan (6-Day Scope)

## 1. Preserved Tickets (Unchanged)
- **TICKET-01**: User Authentication & JWT Service (DONE)
- **TICKET-02**: Provider Profile & Catalog API (DONE)
- **TICKET-03**: Provider Slot Availability API (DONE / Branch ready)

## 2. Modified Tickets
- **TICKET-04 (Booking Creation API)**:
  - *Modification*: Extend payload to support `booked_for_name` (string, optional) and `booked_for_email` (string, optional). Add validation logic when `can_book_for_others` is true.

## 3. Cut Tickets (Deferred post-demo)
- **CUT-01 (Advanced Search & Fuzzy Category Matching)**: Search operates on direct category and city filters; fuzzy matching is non-essential for initial pilot.
- **CUT-02 (Provider Earnings & Analytics Dashboard)**: Providers view raw booking history; financial aggregated charts deferred.

## 4. Added Tickets
- **TICKET-07 (Corporate Delegation Data Bridge & UI)**:
  - *Scope*: Add `company_name` and `can_book_for_others` columns to User model, and implement delegate booking inputs on the booking confirmation UI.
  - *Estimate*: Small (1 day).
