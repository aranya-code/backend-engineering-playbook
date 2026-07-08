# IAM Policies

How IAM policies are structured, how AWS evaluates them, and the guardrail mechanisms that cap what policies can grant.

---

# Topics Covered

| # | Topic | Key Concepts |
|---|-------|-------------|
| 01 | [Policy Basics](./01-%20Policy%20Basics.md) | What a policy is, identity-based vs resource-based, where policies can be attached |
| 02 | [IAM Policy Structure](./02-%20IAM%20Policy%20Structure.md) | Every JSON element explained — Effect, Action, Resource, Condition — with annotated example |
| 03 | [Inline vs Managed Policies](./03-%20Inline%20vs%20Managed%20Policies.md) | Reusability, versioning, limits, and when to use each type |
| 04 | [Policy Examples](./04-%20Policy%20Examples.md) | Four annotated real-world examples: S3 access, cross-account, permission boundary, conditional |
| 05 | [Policy Evaluation Logic](./05-%20Policy%20Evaluation%20Logic.md) | The exact order AWS resolves multiple policies into one Allow/Deny decision |
| 06 | [Permission Boundaries and SCPs](./06-%20Permission%20Boundaries%20and%20SCPs.md) | Two guardrail mechanisms that cap (never grant) permissions |
| 07 | [ABAC](./07-%20Attribute-Based%20Access%20Control%20(ABAC).md) | Tag-based permissions that scale without writing a new policy per team or resource |

---

# Policy Evaluation Flow

```text
Request Arrives
      │
      ▼
Explicit Deny in ANY policy?  ──YES──►  DENIED
      │ NO
      ▼
SCP allows? (if in Organization)  ──NO──►  DENIED
      │ YES
      ▼
Resource-based policy allows?  ──YES──►  ALLOWED (cross-account)
      │ NO
      ▼
Permission Boundary allows?  ──NO──►  DENIED
      │ YES
      ▼
Identity-based policy allows?  ──YES──►  ALLOWED
      │ NO
      ▼
DENIED (default deny)
```

---

# Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [IAM Module](../README.md) |
| ➡️ Next | [Roles](../02-%20Roles/) |

---

*Part of the [Backend Engineering Playbook](../../../../) — Aranya Majumdar*
