# Module 06: Break Diagnosis - Contract Violation Detection

## Detected Rogue Agent Violations
1. **Agent 03 (Frontend Client UI)**:
   - *Violation*: Submitting integer ID (`slot_id: 1042`) instead of UUID string (`slot_id: "slt_aabbccddeeff0011"`).
   - *Impact*: Fails API validation in Agent 02 Booking Creation endpoint.

2. **Agent 02 (Booking Creation API)**:
   - *Violation*: Output enum case drift (`status: "CONFIRMED"` vs contract specification `status: "confirmed"`).
   - *Impact*: Client UI logic evaluating `status === "confirmed"` renders "unknown state".

## Remediation Strategy
- Enforce strict JSON schema validation / TypeScript interface compilation prior to branch merges.
