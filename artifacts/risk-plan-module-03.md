# Risk-First Build Plan: SkillSwap Platform Decomposition

## Part 1: Annotated Work Item Inventory

| Node / Work Item | Risk Score (1-5) | Risk Types | Risk Description & Unknowns |
| :--- | :---: | :--- | :--- |
| **1. Payment Processing Spike & Integration** | **5** | Integration, Dependency | Third-party Stripe API contract, webhook idempotency, 15% escrow hold & split payout, dispute & refund lifecycle. External blocker for revenue. |
| **2. Booking Engine & Slot Concurrency** | **4** | Novelty, Integration | Race conditions when concurrent users book the same provider time slot. Requires optimistic locking / transactional isolation. |
| **3. Multi-City Geographic Expansion & Search** | **3** | Scale, Novelty | 5-city expansion in 6 months. Spatial indexing, latency budget ("feel instant" <200ms), city-scoped data partitioning. |
| **4. Provider Vetting & Onboarding State Machine** | **3** | Novelty, Dependency | Multi-step state lifecycle (`DRAFT` -> `PENDING_REVIEW` -> `APPROVED` / `REJECTED`), credential verification, and status triggers. |
| **5. Core User & Session Infrastructure (Auth)** | **2** | Dependency | JWT authentication, RBAC (Consumer, Provider, Admin). Well-understood pattern, low novelty, but foundational dependency. |
| **6. Provider Profile & Listing Data Model** | **2** | Dependency | Service categories, hourly rates, availability calendar schema. Foundational for booking and search. |
| **7. Minimal Admin Review Tool (API/CLI)** | **2** | Dependency | Single headless endpoint `POST /api/admin/providers/:id/approve` unblocking the onboarding critical path. |
| **8. Ratings & Review Aggregation** | **2** | Scale | Post-service review submission, average score calculation, provider search ranking signals. |
| **9. Consumer Profile & History UI** | **1** | None Significant | Standard CRUD form, profile editing, historical booking view. |
| **10. Full Admin Dashboard & Metrics** | **1** | Scale | Analytics charts, dispute manager UI, revenue metrics. Nice-to-have operational tooling, non-blocking. |

---

## Part 2: Risk-First Numbered Build Order

### 1. Minimal User Auth & Role Infrastructure
- **Risk Score:** 2 (Dependency)
- **Justification:** Hard foundation required to identify actors (Consumer, Provider, Admin) across all downstream transactional and payment routes.

### 2. Provider Data Schema (Pending & Active States)
- **Risk Score:** 2 (Dependency)
- **Justification:** Establishes the data structures needed for provider onboarding, search, and booking workflows without circular locks.

### 3. Payment Processing Technical Spike (Stripe Connect & Webhooks)
- **Risk Score:** 5 (Integration Risk — Highest Unknown)
- **Justification:** Drill the test well immediately. Validates Stripe payment intent creation, customer charge authorization, webhook receipt, and 15% platform fee deductions before building product UI.

### 4. Booking Concurrency & Time-Slot Isolation Engine
- **Risk Score:** 4 (Novelty Risk — Concurrency & Race Conditions)
- **Justification:** Second highest technical unknown. Solves double-booking prevention under concurrent requests using database transaction isolation (`SELECT ... FOR UPDATE` or optimistic versioning) coupled with payment holds.

### 5. Minimal Admin Approval Endpoint (CLI/API)
- **Risk Score:** 2 (Dependency)
- **Justification:** Unblocks provider activation on the critical path without waiting for a complex front-end admin suite.

### 6. Provider Onboarding & Credential Vetting Workflow
- **Risk Score:** 3 (Novelty / State Transitions)
- **Justification:** Implements end-to-end provider registration, credential uploads, and approval state transitions.

### 7. City-Aware Provider Search & Spatial Indexing
- **Risk Score:** 3 (Scale / Latency)
- **Justification:** Builds geospatial and category search with composite indices to fulfill the sub-200ms latency requirement across multiple launch cities.

### 8. Payout Execution & Refund Lifecycle Integration
- **Risk Score:** 4 (Integration / Financial Invariants)
- **Justification:** Connects completed bookings to provider bank transfer payouts and automated cancellation refund paths.

### 9. Consumer Booking UI & Review System
- **Risk Score:** 2 (CRUD / Low Novelty)
- **Justification:** Standard client-facing booking interface and feedback submission loop.

### 10. Full Admin Dashboard & Operational Analytics
- **Risk Score:** 1 (Non-Blocking / Polish)
- **Justification:** Built in parallel once all underlying business data streams (users, bookings, payments) exist and are verified.
