# IAM Troubleshooting

Debugging the two most common IAM failure modes (Access Denied and AssumeRole errors), and the tools that catch permission problems before they reach production.

---

# Topics Covered

| # | Topic | Key Concepts |
|---|-------|-------------|
| 01 | [Access Denied](./01-%20Access%20Denied.md) | Common causes ranked by likelihood, step-by-step debugging sequence |
| 02 | [STS AssumeRole Errors](./02-%20STS%20AssumeRole%20Errors.md) | Trust policy, permission, and ExternalId issues |
| 03 | [Policy Simulator and Debugging Tools](./03-%20Policy%20Simulator%20and%20Debugging%20Tools.md) | Testing policy changes before deploying, validating policies as you write them |

---

# Troubleshooting Decision Tree

```text
Error Received
      │
      ├── "Access Denied" ──────────────────────► See 01- Access Denied.md
      │     │
      │     ├── Check identity-based policy (does the user/role have the permission?)
      │     ├── Check resource-based policy (does the resource allow the caller?)
      │     ├── Check permission boundary (is it capping the effective permissions?)
      │     ├── Check SCP (is the Organization blocking the action?)
      │     └── Check condition keys (is MFA required? IP restriction? Wrong region?)
      │
      ├── "Not authorized to perform sts:AssumeRole" ──► See 02- STS AssumeRole Errors.md
      │     │
      │     ├── Trust policy: is the calling principal listed?
      │     ├── Caller permission: does the caller have sts:AssumeRole permission?
      │     └── ExternalId: is it required and was it provided?
      │
      └── "Not sure which policy is causing the issue" ──► See 03- Policy Simulator.md
            │
            ├── Use IAM Policy Simulator (test before deploying)
            ├── Use CloudTrail (find the exact API call that was denied)
            └── Use --decode-authorization-message (decode the error context)
```

---

# Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [IAM Module](../README.md) |
| ⬅️ Previous | [Monitoring](../04-%20Monitoring/) |
| ➡️ Next | [Interview](../06-%20Interview/) |

---

*Part of the [Backend Engineering Playbook](../../../../) — Aranya Majumdar*
