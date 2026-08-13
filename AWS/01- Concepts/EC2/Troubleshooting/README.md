# Troubleshooting

Real EC2 failure modes, with the specific signal each one gives you and a step-by-step debugging sequence.

---

| # | Topic | Description |
|---|-------|-------------|
| 01 | [Connection Refused](01-%20Connection%20Refused.md) | The network layer is fine — the app itself isn't listening correctly |
| 02 | [Connection Timeout](02-%20Connection%20Timeout.md) | Security Group, NACL (both directions), or routing — in that order |
| 03 | [Instance Failing Health Checks](03-%20Instance%20Failing%20Health%20Checks.md) | Target Group vs. ASG health checks, and why they can disagree |
| 04 | [High CPU and T-Series Throttling](04-%20High%20CPU%20and%20T-Series%20Throttling.md) | Diagnosing CPU credit exhaustion before it looks like a mystery slowdown |

---

## 🔗 See Also

- [`../`](../) — EC2 overview
- [`../Networking`](../Networking) — the security groups and NACLs these issues most often trace back to

---

*Part of the [backend-engineering-playbook](../../../../) knowledge base — Aranya Majumdar*
