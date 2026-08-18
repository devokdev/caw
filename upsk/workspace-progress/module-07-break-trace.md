# Module 07 BREAK — The Privilege Escalation: Trace

Scenario: a viewer on a team became an admin without any admin action.

## The canonical exploit the module warns about

`PATCH /teams/{id}/members/{uid}/role` — if the authorization check were
"is this user a team member" instead of "is this user an owner/admin", then a
viewer (who IS a member) could send `{ "role": "admin" }` for their own member
record and be promoted. Combined with a missing `role` enum validation, that is
a critical privilege escalation composed of two individually-medium findings.

## Trace of every role-write path in this codebase

Only three code paths ever write `TeamMember.role`:

| Path | Auth check on route | Result for a viewer |
|---|---|---|
| `POST /teams/{id}/members` (`add_member`) | `require_owner_or_admin` | **403** (viewer is neither owner nor admin) |
| `PATCH /teams/{id}/members/{uid}/role` (`update_member_role`) | `require_owner` | **403** (viewer != team owner) |
| `POST /teams/{id}/invitations/{token}/accept` (`accept_invitation`) | token + email match | role hardcoded `ROLE_MEMBER` — cannot produce admin |

Additionally, `AddMemberRequest.role` and `UpdateRoleRequest.role` are
`Literal["admin", "member", "viewer"]` (Pydantic), so an invalid value like
`"superadmin"` is rejected with 400 before reaching the service.

## Live probe (evidence)

- `PATCH /teams/{tid}/members/{bob_uid}/role {"role":"admin"}` as bob (viewer) → **403** `team owner required`
- `POST /teams/{tid}/members {email: bob, role: admin}` as bob → **403** `team admin required`
- `POST /teams/{tid}/invitations` as bob → **403**
- `DELETE /teams/{tid}/invitations/999` as bob → **403**
- `DELETE /teams/{tid}/members/{owner_uid}` as bob → **403**

## Conclusion

The escalation vector **does not exist** in the current codebase: the role
mutation endpoint enforces `require_owner` (stricter than the module's
canonical "checks membership" pattern) and the role field is enum-validated.
This is the payoff of the system-level review — the composition that would
otherwise be critical ("membership check + unvalidated role = self-promotion")
was broken at both links in Module 4's fixes and confirmed here.

The regression tests that pin this behavior:
`test_admin_can_add_member_but_not_change_roles`,
`test_update_role_owner_only`, `test_remove_member_owner_only`.