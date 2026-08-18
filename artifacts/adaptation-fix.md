# Module 07: Fix - Final Layered Adaptation Architecture

## 1. Role-Based Access Control Architecture

```
User (Token Claims)
 ├── id: uuid
 ├── org_id: uuid
 ├── department_id: uuid
 └── role: 'employee' | 'manager' | 'dept_head' | 'admin'
```

### Authorization Enforcement Rules:
1. **Manager**: Can issue `POST /api/v1/bookings` with `booked_for_user_id` belonging to any user in the same `org_id`.
2. **Employee**: Restricted to `booked_for_user_id == current_user.id`. Any delegation attempt returns `HTTP 403 Forbidden` (`INSUFFICIENT_ROLE_PERMISSIONS`).
3. **Department Head**: Authorized for `GET /api/v1/bookings?dept_id={department_id}` viewing all team bookings in their department.

---

## 2. Revised Impact Statement to PM

**To**: Product Management  
**From**: Lead Engineering  
**Subject**: Revision 2: Scope & Schedule Update with RBAC Multi-Tenancy  

Following our initial 6-day projection, Meridian's additional requirement for hierarchical role-based access control (Manager booking delegation, Employee self-service restrictions, and Department Head visibility) fundamentally expands the security and data boundaries. To deliver a secure, production-grade RBAC pilot within the 6-day investor milestone, we are scoping the core 3 roles directly into our JWT authorization middleware and booking APIs. In exchange, we must strictly defer all provider earnings analytics and advanced search filters to the post-demo sprint. The primary delivery dependency remains confirming Meridian's department taxonomy schema by Day 2.
