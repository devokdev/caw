# TICK-001: Seed Database with Test Provider & Slot Data

## 1. Title
`TICK-001: Seed Database with 3 Test Providers & Availability Slots`

## 2. Context (Why)
To enable the demand-side MVP (Slice 1) without waiting for provider registration forms and admin vetting flows to be built, the marketplace needs reliable, realistic seeded data representing 3 distinct service providers and their open booking slots.

## 3. Scope (What)
Create a migration/seeding script (`src/db/seeds/01_providers.ts` or `.sql`) that populates the PostgreSQL database with:
- 3 approved providers (Guitar Tutoring, Python Mentoring, Yoga Training)
- 3 distinct time slots for each provider for today/tomorrow with `status = 'AVAILABLE'`

## 4. Interface Contract
### Seed Schema Structure:
- `providers` table:
  - `id`: UUID (v4)
  - `name`: String (e.g. "Alice Guitar Tutoring", "Bob Python Mentoring", "Carla Yoga")
  - `category`: String ("MUSIC", "TECH", "WELLNESS")
  - `hourly_rate_cents`: Integer (5000 = $50.00)
  - `rating`: Decimal (5.0)
  - `status`: String ("APPROVED")
- `availability_slots` table:
  - `id`: UUID (v4)
  - `provider_id`: UUID (FK to providers)
  - `start_time`: ISO 8601 Timestamp
  - `end_time`: ISO 8601 Timestamp (start_time + 1 hour)
  - `status`: String ("AVAILABLE" | "BOOKED")

## 5. Acceptance Criteria (Given/When/Then)
- **AC-1:** Given an empty database, When the seed script `npm run db:seed` executes, Then 3 provider records exist in `providers` with `status = 'APPROVED'`.
- **AC-2:** Given seeded providers, When querying `availability_slots`, Then exactly 9 slots exist (3 per provider) with `status = 'AVAILABLE'`.
- **AC-3:** Given repeated executions of `npm run db:seed`, When the script runs, Then it executes idempotently without duplicate key violation errors.

## 6. Constraints
- Use standard SQL / existing Knex/Prisma/pg client in `src/db`.
- All IDs must be deterministically generated or standard UUID v4 strings.
- Times must be normalized to UTC.

## 7. Anti-Scope
- No REST API endpoints (data layer seeding only).
- No image upload or CDN asset hosting (use mock SVG avatars / placeholder URLs).
- No dynamic cron schedule for generating slots.
