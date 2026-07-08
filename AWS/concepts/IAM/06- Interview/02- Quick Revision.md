# Quick Revision

## Fundamentals
- IAM is a **global** service — no regional scope
- Authentication = who you are; Authorization = what you can do
- Root account has unrestrictable permissions — no policy can limit it

## Users, Groups, Roles
- Groups contain **users only** — cannot nest groups, cannot be assumed
- Roles have **no long-term credentials** — only temporary, via STS
- A user can belong to multiple groups; effective permissions are the union of all attached policies

## Policies
- Structure: `Version`, optional `Id`, one or more `Statement`s
- Each statement: `Effect`, `Action`, `Resource`, optional `Principal` (resource-based only) and `Condition`
- **Explicit Deny always wins** — overrides any Allow, from any policy, at any layer
- Identity-based (attached to identity) vs. resource-based (attached to resource, has a `Principal`)
- Inline (one-off, not reusable) vs. Managed (reusable, versioned)

## Policy Evaluation Order
1. Implicit deny by default
2. SCPs — any deny ends evaluation immediately
3. Resource-based, identity-based, permission boundary, session policies evaluated
4. Any explicit Deny anywhere → denied
5. At least one explicit Allow, no Deny found → allowed

## Permission Boundaries vs. SCPs
- Permission boundary: caps ONE user/role; effective = policy ∩ boundary
- SCP: caps entire account(s)/OU via AWS Organizations; applies even to root

## Roles
- Two policies: **Trust policy** (who can assume) + **Permission policy** (what they can do once assumed)
- Instance profile = the container that actually attaches a role to an EC2 instance
- Cross-account: target role's trust policy names the source account/role; `ExternalId` guards against confused-deputy risk

## Security
- MFA: virtual (TOTP) > SMS (SIM-swap risk); enforce via `aws:MultiFactorAuthPresent` condition, not just convention
- Least privilege: start narrow, use Access Advisor + Access Analyzer to trim over time
- Rotate credentials on a schedule; prefer roles/federation to eliminate long-term credentials entirely
- Access Analyzer = finds unintended **external** access + generates least-privilege policies from activity

## Monitoring
- Access Advisor = per-identity, what's **actually used** vs. granted (inward-looking)
- Credentials Report = account-wide CSV of every user's credential status (passwords, keys, MFA)

## Troubleshooting
- AccessDenied → check identity policy, permission boundary, SCPs, resource-based policy, in that rough order
- AssumeRole errors → check trust policy Principal, caller's own `sts:AssumeRole` permission, ExternalId, session duration
- Policy Simulator tests a hypothetical request without making the real API call
