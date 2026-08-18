# Module 07: Break Analysis - Layering RBAC Requirements

## 1. Updated Blast Radius Assessment (Layer 2 Adaptation)

| Artifact | Previous Status | New Status & Escalation | Impact Breakdown |
|---|---|---|---|
| User Data Model | MINOR | MAJOR | Must support `role` enum (`employee`, `manager`, `dept_head`, `admin`), `organization_id` FK, and `department_id` FK. |
| Auth / JWT System | NO IMPACT | MAJOR | JWT payload must now encode `org_id`, `role`, and `dept_id` claims to allow stateless authorization checks. |
| Booking Flow (API) | MAJOR | MAJOR | Enforce policy authorization layer: Managers can book for any org user; Dept Heads can query all department bookings; Employees can only view/create self-bookings. |
| Booking Flow (UI) | MINOR | MAJOR | Role-aware conditional views (Manager booking widget vs Dept Head overview table). |
| Provider Dashboard | MINOR | MINOR | Booking details show attendee name and organization name. |

---

## 2. Decision Review: Why Option B Breaks & Option A+ Emerges
- The minimal bridge (Option B boolean flag `can_book_for_others`) cannot satisfy 3 distinct hierarchical roles (`manager`, `employee`, `dept_head`) with departmental boundaries.
- **Architectural Pivot**: We pivot to a scoped relational organization/department schema with role claims in the JWT token.
