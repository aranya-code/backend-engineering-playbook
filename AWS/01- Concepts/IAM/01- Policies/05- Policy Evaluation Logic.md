# Policy Evaluation Logic

When a request is made, AWS may have several applicable policies to consider — identity-based, resource-based, permission boundaries, and Service Control Policies. Understanding exactly how these combine into one Allow/Deny decision is one of the most consequential pieces of IAM knowledge, and a very common source of "why can't this identity do the thing I clearly gave it permission for" confusion.

## The Evaluation Order

```text
1. Default: Deny (implicit deny — nothing is allowed unless explicitly granted)
2. Organization SCPs evaluated — if any SCP denies it, request is denied. Full stop.
3. Resource-based policies evaluated (if applicable)
4. Identity-based policies evaluated
5. IAM permission boundaries evaluated (if set on the identity)
6. Session policies evaluated (if passed when assuming a role)
7. If ANY explicit Deny is found at any layer above → DENIED, immediately, no exceptions
8. If at least one explicit Allow exists, and no Deny was found → ALLOWED
9. If nothing explicitly allowed it → DENIED (the implicit default)
```

## The One Rule That Matters Most: Explicit Deny Always Wins

No matter how many policies grant `Allow`, a single explicit `Deny` anywhere in the evaluation — an SCP, a permission boundary, an identity-based policy, a resource-based policy — overrides all of them. There is no mechanism to "override a deny" from a different policy; the only fix is removing or narrowing the deny itself.

## Cross-Account Requests Need Both Sides to Agree

For a request from Account A to a resource in Account B: Account A's identity-based policy must allow the action, **and** Account B's resource-based policy must allow that principal from Account A. Either side alone is not sufficient — this is the single most common cause of "access denied" in cross-account setups, and the first thing worth checking when debugging one.

## Permission Boundaries Set a Ceiling, Not a Grant

A permission boundary doesn't grant any permissions by itself — it defines the **maximum** an identity-based policy is allowed to grant. The effective permission is always the intersection of the permission boundary and the identity-based policy, never the union. This is a common point of confusion: adding a broader permission boundary doesn't grant new access; it only raises the ceiling for what the identity-based policy is *allowed* to grant.

## A Concrete Walkthrough

A role has:
- An identity-based policy allowing `s3:*` on all resources
- A permission boundary limiting it to `s3:GetObject` and `s3:ListBucket` only
- No applicable SCP denies

**Result:** the role can only `GetObject` and `ListBucket` — the permission boundary caps the identity policy's broader grant down to its own more restrictive intersection, even though the identity-based policy itself would have allowed much more.

## Senior-Level Considerations

- When troubleshooting an unexpected deny, check every layer in order — SCPs (if in an Organization), the resource-based policy (if applicable), the identity-based policy, and any permission boundary — rather than assuming the identity-based policy is the only thing to inspect
- AWS's own IAM Policy Simulator (see the Troubleshooting section) can evaluate this full chain for a hypothetical request without actually making it — genuinely useful for confirming a Allow/Deny outcome before deploying a policy change to production
- "Explicit deny always wins" is one of the most commonly tested interview facts about IAM, precisely because it has real, frequent practical consequences
