# Policy Basics

## What Is an IAM Policy?

A JSON document that defines permissions — which actions are allowed or denied on which resources, and under what conditions. Policies are the actual mechanism that turns "this user exists" into "this user can do X."

## Policies Attach To, Not Belong To

A policy is a standalone object — the same managed policy can be attached to many different users, groups, or roles simultaneously. This is a deliberate design: define the permission set once, attach it wherever needed, rather than rewriting the same JSON repeatedly.

## Where Policies Can Be Attached

| Attached To | Effect |
|---|---|
| User | Permissions apply directly to that user |
| Group | Permissions apply to every user in the group |
| Role | Permissions apply to whoever assumes the role |
| Resource (resource-based policy) | Permissions apply to whoever the policy names as principal, regardless of which account they're in |

## Identity-Based vs. Resource-Based Policies

- **Identity-based** — attached to a user, group, or role ("this identity can do X")
- **Resource-based** — attached directly to a resource, like an S3 bucket policy or an SQS queue policy ("this resource allows access from these principals")

Both can apply to the same request simultaneously — for cross-account S3 access, for instance, the accessing role needs an identity-based policy allowing the action, **and** the bucket's resource-based policy needs to allow that external account/role. Missing either one results in denied access, which is a very common real-world debugging trap.

## Senior-Level Considerations

- Policies are evaluated, not just "attached" — see `Policy Evaluation Logic.md` for exactly how AWS resolves multiple applicable policies into a single Allow/Deny decision
- Because the same managed policy can be attached in many places, a change to a widely-attached managed policy has a blast radius equal to everywhere it's attached — a good reason to understand a policy's attachment list before editing it
