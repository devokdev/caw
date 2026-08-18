# SkillSwap Extracted Requirements Matrix (Module 01)

## Overview
Categorized requirements matrix for SkillSwap marketplace across stakeholder types and taxonomy classifications.

---

## 1. USER Requirements

### Functional Requirements
1. **REQ-U-01**: Users can browse and filter providers by predefined and searchable categories. *(Source: Para 1, Explicit, Confidence: High)*
2. **REQ-U-02**: Users can view detailed provider profiles displaying services, hourly rates, verified badges, and aggregated star ratings with reviews. *(Source: Para 1, Explicit, Confidence: High)*
3. **REQ-U-03**: Users can view real-time available time-slots on a provider calendar. *(Source: Para 1, Explicit, Confidence: High)*
4. **REQ-U-04**: Users can reserve a time slot, execute payment through platform escrow/gateway, and receive instant booking confirmation. *(Source: Para 1, Explicit, Confidence: High)*
5. **REQ-U-05 [BLOCKED - Pending PM Decision on Policy Hierarchy]**: Users can cancel booked sessions subject to resolved platform vs provider cancellation policy.
   - **Option 1 (Platform Universal)**: Universal 24h full refund window; non-refundable thereafter. High user consistency, lower provider autonomy.
   - **Option 2 (Provider Policy with Platform Floor)**: 1-hour cooling-off full refund guaranteed by platform; provider custom cancellation tiers apply thereafter. Balances user safety net and provider schedule protection.
   - *Affected Areas*: Payment capture & escrow release, automated refund processing, provider earnings dashboard, provider onboarding policy editor.
6. **REQ-U-06**: Users can submit ratings and written reviews after a session is marked completed. *(Source: Para 1 & 2, Implicit, Confidence: High)*

### Quality Attributes
7. **REQ-U-QA-01**: Provider catalog search and filtering must return results with sub-200ms p95 latency under concurrent traffic ("feel instant"). *(Source: Para 1 & 3, Explicit, Confidence: High)*
8. **REQ-U-QA-02**: Booking flow must provide atomic slot reservation to prevent race conditions / double-booking under concurrent load. *(Source: Canonical Constraints, Explicit, Confidence: High)*

---

## 2. PROVIDER Requirements

### Functional Requirements
9. **REQ-P-01**: Providers can create and manage public profiles, biography, credentials, service offerings, and pricing. *(Source: Para 2, Explicit, Confidence: High)*
10. **REQ-P-02**: Providers can configure recurring and custom availability calendar slots, buffer times, and maximum daily sessions. *(Source: Para 2, Explicit, Confidence: High)*
11. **REQ-P-03**: Providers can define their specific cancellation policy tier (contingent on resolution of REQ-U-05). *(Source: Para 1 & 2, Explicit, Confidence: Medium)*
12. **REQ-P-04**: Providers have access to a dashboard displaying incoming bookings, earnings summaries, payout status, and client reviews. *(Source: Para 2, Explicit, Confidence: High)*
13. **REQ-P-05**: Providers can flag no-show clients to platform ops for penalty/payout protection. *(Source: Para 2, Explicit, Confidence: High)*

### Constraints
14. **REQ-P-C-01**: Platform automatically deducts a 15% platform commission on all gross session bookings before provider net payout balance is calculated. *(Source: Para 2, Explicit, Confidence: High)*
15. **REQ-P-C-02**: New providers must undergo a vetting and approval workflow by platform admin before listings become publicly searchable. *(Source: Para 2 & 3, Explicit, Confidence: High)*

---

## 3. PLATFORM & OPS Requirements

### Functional Requirements
16. **REQ-OPS-01**: Admin dashboard for vetting, approving, suspending, or rejecting provider onboarding applications. *(Source: Para 2 & 3, Explicit, Confidence: High)*
17. **REQ-OPS-02**: Dispute resolution system allowing ops agents to review flagged sessions, view chat/booking logs, and issue full/partial refunds or overrides. *(Source: Para 3, Explicit, Confidence: High)*
18. **REQ-OPS-03**: Automated notification engine sending transactional emails and reminders (booking confirmation, cancellation notice, payout receipt). *(Source: Para 1, Explicit, Confidence: High)*
19. **REQ-OPS-04**: Platform telemetry and event analytics tracking search queries, conversion rates, booking drop-offs, GMV, and dispute rates. *(Source: Para 3, Explicit, Confidence: High)*
20. **REQ-OPS-05**: Automated or batch payout pipeline disbursing net balances (85%) to verified provider bank accounts. *(Source: Para 2, Implicit, Confidence: High)*

### Quality Attributes & Constraints
21. **REQ-OPS-QA-01**: Multi-city tenancy architecture allowing geographic expansion to 5 cities within 6 months without schema redesign or downtime. *(Source: Para 3, Explicit, Confidence: High)*
22. **REQ-OPS-QA-02**: System must sustain baseline load of at least 5,000 active concurrent users per regional cluster. *(Source: Para 3, Explicit, Confidence: High)*

---

## 4. Ambiguities & Open Questions for PM

1. **Cancellation & Refund Structure**: What are the standardized platform cancellation tiers providers can select from, and does platform policy override provider terms?
2. **City Partitioning & Localization**: How are cities geographically bounded (e.g. radius around city center vs zip/postal codes), and do pricing/taxes vary across cities?
3. **Escrow & Payout Schedule**: When are booking funds released to the provider's payout balance (e.g. immediately upon session end, or T+3 days dispute hold window)?
