# Permission Boundaries and Service Control Policies (SCPs)

Both are guardrail mechanisms that *limit* what identity-based policies can grant — but they operate at different scopes and are frequently confused with each other.

## Permission Boundaries

An advanced IAM feature that sets the **maximum permissions an identity-based policy can grant to a single user or role**. Attached directly to that specific user or role.

```text
Effective Permissions = Identity-Based Policy ∩ Permission Boundary
```

**Common use case:** allowing a team to create their own IAM roles for their applications, while ensuring none of those self-created roles can ever exceed a defined ceiling (e.g., "no role this team creates can ever touch IAM or billing, no matter what permissions they attach to it").

## Service Control Policies (SCPs)

Operate at the **AWS Organizations level**, applied to entire accounts or Organizational Units — not to individual users or roles. An SCP restricts what's possible for **every identity in every affected account**, including that account's own root user and administrators.

```text
Effective Permissions (org-wide) = Identity-Based Policy ∩ All Applicable SCPs
```

**Common use case:** "no account in this Organization may disable CloudTrail," "no account may create resources outside approved Regions," "no account may leave the Organization" — guardrails meant to apply uniformly regardless of how any individual account's administrators configure IAM.

## Key Differences

| | Permission Boundary | SCP |
|---|---|---|
| Scope | One specific user or role | Entire account(s) / Organizational Unit(s) |
| Requires an Organization? | No | Yes (AWS Organizations feature) |
| Can be bypassed by an account admin? | No (but a different admin can remove/change the boundary itself if they have permission to) | No — SCPs apply even to that account's own root user |
| Typical use | Delegating safe self-service role creation to a team | Company-wide compliance and governance guardrails |

## Neither Grants Anything

This is the most important shared property: both are purely restrictive. Attaching a broad permission boundary or a permissive SCP does not grant any new access on its own — the identity-based policy still has to explicitly grant the permission; the boundary/SCP can only narrow it further, never expand it.

## Senior-Level Considerations

- SCPs are how large organizations enforce security posture structurally, without relying on every account's administrators independently making the same correct decision — this matters enormously at scale, where trusting convention alone doesn't hold up
- A genuinely common senior-level design: use SCPs for org-wide non-negotiable guardrails (region restrictions, preventing CloudTrail from being disabled), and permission boundaries for team-level self-service safety (letting application teams create their own roles within a safe ceiling) — the two mechanisms are complementary, not competing
