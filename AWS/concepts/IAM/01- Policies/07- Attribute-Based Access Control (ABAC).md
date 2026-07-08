# Attribute-Based Access Control (ABAC)

## RBAC vs. ABAC

Everything covered so far in this folder is essentially **role-based access control (RBAC)** — permissions defined by writing (or attaching) a specific policy per role or per group of users. **ABAC** takes a different approach: permissions are granted based on **attributes** (tags) attached to both the principal and the resource, using a single, reusable policy that evaluates those tags at request time rather than needing a dedicated policy per team, project, or resource.

## How It Works

Tags go on two places:

- **Principal tags** — attached to an IAM user or role (e.g., `Team: Payments`)
- **Resource tags** — attached to the resource being accessed (e.g., an EC2 instance tagged `Team: Payments`)

A single ABAC policy then compares the two at request time:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "ec2:*",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:ResourceTag/Team": "${aws:PrincipalTag/Team}"
        }
      }
    }
  ]
}
```

This one policy allows a principal to manage EC2 resources **only if the resource's `Team` tag matches their own `Team` tag** — the same policy works correctly for every team without being edited, because the comparison is dynamic rather than hardcoded to a specific team name.

## Why This Scales Better Than RBAC Alone

Under pure RBAC, adding a new team or project typically means writing (or cloning and modifying) a new policy scoped to that team's specific resources. Under ABAC, the same policy already works — a new team just needs its resources and principals tagged consistently, with no policy authoring required at all. This is exactly why AWS recommends ABAC specifically for organizations with rapidly growing numbers of teams, projects, or resources.

## The Prerequisite: Consistent, Governed Tagging

ABAC's entire security model depends on tags being accurate and not freely editable by the people the policy is meant to restrict — if a user can simply retag a resource to match their own principal tag, they've effectively granted themselves access. This means **tagging itself becomes a security-relevant permission**: `ec2:CreateTags` (and equivalents in other services) needs to be tightly controlled, often restricted to a separate provisioning process or a more trusted role, wherever ABAC is used for real access control.

## Where ABAC Fits Well vs. Where It Doesn't

**Good fit:** large organizations with many teams/projects needing similar access patterns to their own resources, environments with mature tagging discipline already in place (cost allocation tagging, for instance, often provides a foundation to build on).

**Weaker fit:** small accounts with few distinct teams (the overhead of setting up tagging governance may not be worth it yet), or environments where tagging is inconsistent or unenforced — ABAC on ungoverned tags is a security model built on an untrustworthy foundation.

## Senior-Level Considerations

- ABAC and RBAC aren't mutually exclusive — a common real-world pattern combines a small number of RBAC-style baseline policies (broad service access) with ABAC conditions layered on top to scope that access down to a principal's own tagged resources
- `aws:PrincipalTag` and `aws:ResourceTag` are the core condition keys, but AWS also supports tagging on the *request* itself (`aws:RequestTag`) — relevant when the access decision needs to consider a tag being applied as part of the current action, such as only allowing resource creation if it's tagged correctly at creation time
- This is an increasingly common senior-level interview topic specifically because it represents a mindset shift from "write more policies" to "design a permission model that scales without more policies" — a distinction that signals real architectural thinking about IAM rather than just policy-writing familiarity
