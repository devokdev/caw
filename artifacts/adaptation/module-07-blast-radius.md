# Module 07: Blast Radius Analysis

## Part 1: Company Accounts Requirement Blast Radius

| Artifact | Status | Impact | Detailed Impact Description |
|---|---|---|---|
| User Data Model | Active | MINOR | Add nullable `company_name` (varchar) and `can_book_for_others` (boolean default false). |
| Auth / JWT System | Done | NO IMPACT | Existing JWT claims unchanged; user identity remains tied to primary account `user_id`. |
| Booking Flow (API) | Active | MAJOR | Update `POST /api/v1/bookings` schema to accept optional `booked_for_name` and `booked_for_email`. Validate presence if user has `can_book_for_others=true`. Return delegated booking metadata. |
| Booking Flow (UI) | Active | MINOR | Render conditional input fields ("Booking for someone else?") on the checkout screen when profile flag is set. |
| Provider Dashboard | Planned | MINOR | Display `booked_for_name` in the booking details modal so providers know who is attending the session. |
| Search / Listing | Done | NO IMPACT | Provider filtering and listing endpoints unaffected by corporate delegation attributes. |
| Payment / Billing | Planned | NO IMPACT | Charges remain attached to the booking user's credit card/Stripe customer object. |
| Interface Contracts | Active | MINOR | Add optional `booked_for` schema properties to `module-06-interface-contracts.md`. |
| Completed Tickets (TICKET-01, 02, 03) | Done | NO IMPACT | Preserved as-is without code churn. |
| In-Progress Tickets (TICKET-04) | In Progress | MINOR | Amend booking creation schema to accept and persist delegation fields. |
| Not-Started Tickets (TICKET-05, 06) | Not Started | NO IMPACT | Notification and Review tickets accommodate `booked_for_email` for confirmation dispatch. |

---

## Part 2: Compressed Timeline Categorization (6-Day Scope)

- **MUST SHIP**:
  - TICKET-03 (Provider Availability API)
  - TICKET-04 (Booking Creation API with delegation support)
  - TICKET-07 (Corporate Delegation Booking UI & Schema Bridge)
- **SHOULD SHIP**:
  - TICKET-05 (Email Notification Service with `booked_for_email` recipient routing)
- **CUT**:
  - Advanced Provider Analytics Dashboard (Defers to post-demo milestone)
  - Multi-tier Provider Search Filters (Defers to post-demo milestone)
