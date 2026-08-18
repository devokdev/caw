# Vertical Slices Specification: SkillSwap Marketplace

## Slice 1: Browse and Book (Demand-Side MVP)
- **Scope:**
  - Landing page listing 3 seeded service providers with category, hourly rate, and rating.
  - Provider detail view rendering single service description and 3 available time slots.
  - Time-slot selection and "Book Now" CTA creating a persisted booking record in database.
  - Confirmation screen displaying unique Booking Reference ID, provider name, date/time, and status (`CONFIRMED`).
- **Anti-Scope:**
  - No user authentication or login (anonymous booking session).
  - No real payment processing (free booking hold via in-memory stub).
  - No email / SMS confirmation dispatch (on-screen confirmation only).
  - No dynamic search, city filters, or category sorting (static curated list).
  - No provider portal or self-service listing creation (database seed only).
  - No booking modification, cancellation, or refund workflow.
  - No consumer ratings or review submission.
  - No multi-city partitioning.
  - No admin approval dashboard.
- **Dependencies:** None (Greenfield Slice 1).
- **Acceptance Criteria:**
  1. Navigate to `/` -> View 3 provider cards (e.g., "Alice Guitar Tutoring", "Bob Python Mentoring", "Carla Yoga").
  2. Click "Bob Python Mentoring" -> View provider page with 3 selectable slots (10:00 AM, 2:00 PM, 4:00 PM).
  3. Select "2:00 PM" and click "Book Now".
  4. Redirected to `/booking/confirmation` showing unique Reference ID `#SK-1001`, Provider Name, and Slot Time.
  5. Refreshing `/booking/confirmation?id=SK-1001` retrieves the persisted booking.
- **Estimated Complexity:** S (2–3 hours)

---

## Slice 2: User Authentication & Profile Scoping
- **Scope:**
  - Consumer and Provider sign-up/login via email and password with JWT session storage.
  - Role-based scoping: Consumer views their personal booking history (`/my-bookings`); Provider views incoming bookings.
  - Booking in Slice 1 now associates authenticated `consumer_id` with the transaction.
- **Anti-Scope:**
  - No OAuth (Google/GitHub) social logins.
  - No password reset / email verification tokens.
  - No provider profile self-editing (managed via backend seed/admin).
  - No payment or payout execution.
- **Dependencies:** Slice 1 (Browse and Book).
- **Acceptance Criteria:**
  1. Register consumer account `user@test.com` and log in.
  2. Complete booking from Slice 1 while authenticated.
  3. Navigate to `/my-bookings` and verify the new booking appears under `user@test.com`.
- **Estimated Complexity:** S (3–4 hours)

---

## Slice 3: Provider Self-Service & Onboarding State Machine
- **Scope:**
  - Provider registration flow capturing bio, service categories, pricing, and availability slots.
  - Onboarding state transition: `DRAFT` -> `PENDING_REVIEW` -> `APPROVED`.
  - Minimal Admin review endpoint (`POST /api/admin/providers/:id/approve`) to activate providers.
  - Once approved, provider dynamically appears in Slice 1 marketplace browsing.
- **Anti-Scope:**
  - No complex document upload/ID background check verification.
  - No rich media / gallery uploads.
  - No complex calendar sync (Google Calendar / iCal).
  - No full admin UI dashboard (endpoint/CLI-driven approval).
- **Dependencies:** Slice 2 (Auth).
- **Acceptance Criteria:**
  1. Sign up as provider `provider@test.com`, submit service listing and 3 time slots.
  2. Verify provider profile is in `PENDING_REVIEW` and not visible on the consumer landing page.
  3. Trigger admin approval -> Profile state updates to `APPROVED`.
  4. Visit consumer landing page -> New provider appears dynamically in the listing.
- **Estimated Complexity:** M (1 day)

---

## Slice 4: Real-Time Booking Concurrency & Slot Locking
- **Scope:**
  - Atomic booking reservation using database row-level locking (`SELECT ... FOR UPDATE`).
  - Real-time slot conflict handling: when one user reserves a slot, it immediately disables for other users.
  - Payment interface integration (mock gateway stub) holding funds on slot lock.
- **Anti-Scope:**
  - No live Stripe charge execution (mock adapter).
  - No automated refund dispute workflows.
  - No WebSocket push notifications (REST polling / atomic check on click).
- **Dependencies:** Slice 1, Slice 3.
- **Acceptance Criteria:**
  1. Two parallel browser sessions attempt to book the exact same 2:00 PM slot simultaneously.
  2. Session A succeeds and receives confirmation.
  3. Session B receives an immediate HTTP 409 Conflict error with message "Time slot is no longer available."
- **Estimated Complexity:** M (1 day)

---

## Slice 5: City-Aware Search & Ratings Loop
- **Scope:**
  - Search query bar filtering providers by city (e.g., "Austin", "New York") and category with sub-200ms response.
  - Post-service review submission (1-5 stars and text comment) by consumers after booking completion.
  - Dynamic average rating aggregation updated on provider cards.
- **Anti-Scope:**
  - No full-text Elasticsearch / fuzzy spelling engine (Postgres indexed search).
  - No automated review moderation / profanity filtering.
  - No image reviews.
- **Dependencies:** Slice 2, Slice 3, Slice 4.
- **Acceptance Criteria:**
  1. Filter providers by City: "Austin" -> Returns only Austin-registered approved providers in <200ms.
  2. Submit 5-star review on completed booking -> Provider aggregate rating recalculates instantly.
- **Estimated Complexity:** M (1 day)
