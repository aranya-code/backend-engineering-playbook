# NACL vs Security Group

# Overview

NACLs and Security Groups are both network filtering mechanisms in a VPC, but they operate at different levels, with different behaviors. Understanding both — and when to use each — is critical for senior DevOps engineers.

---

# Where They Sit in the Network Path

```text
Internet
    │
    ▼
Internet Gateway
    │
    ▼
┌─────────────────────────────────────────────┐
│ NACL (Network Access Control List)          │
│ ► Subnet-level firewall                     │
│ ► Stateless (must allow both directions)    │
│ ► Rules evaluated in numbered order         │
│ ► Supports ALLOW and DENY rules             │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ Security Group                              │
│ ► Instance-level (ENI) firewall             │
│ ► Stateful (response auto-allowed)          │
│ ► All rules evaluated together              │
│ ► ALLOW rules only (no deny)                │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
           EC2 Instance
```

---

# Detailed Comparison

| Feature | Security Group | NACL |
|---------|---------------|------|
| Scope | Instance (ENI) level | Subnet level |
| Statefulness | **Stateful** — return traffic auto-allowed | **Stateless** — must explicitly allow return traffic |
| Rule Types | Allow only | Allow AND Deny |
| Rule Evaluation | All rules evaluated (any match = allow) | Rules evaluated in **numbered order** (first match wins) |
| Default Inbound | Deny all | Allow all (default NACL) |
| Default Outbound | Allow all | Allow all (default NACL) |
| Association | Applied to instances (multiple SGs per instance) | Applied to subnets (one NACL per subnet) |
| Applies To | Only instances assigned to the SG | All instances in the subnet automatically |

---

# NACL Rule Evaluation

NACL rules have numbers (1–32766). They are evaluated **lowest number first**, and the **first matching rule wins**.

```text
Rule #  | Type    | Protocol | Port | Source      | Action
────────┼─────────┼──────────┼──────┼─────────────┼────────
100     | HTTP    | TCP      | 80   | 0.0.0.0/0   | ALLOW
200     | SSH     | TCP      | 22   | 10.0.0.0/8  | ALLOW
300     | Custom  | TCP      | 3306 | 0.0.0.0/0   | DENY    ← Block DB from internet
*       | All     | All      | All  | 0.0.0.0/0   | DENY    ← Catch-all (always last)
```

**Best Practice**: Number rules in increments of 100 (100, 200, 300) so you can insert rules between them later.

---

# Ephemeral Ports (Critical for NACLs)

Because NACLs are **stateless**, you must explicitly allow return traffic on ephemeral ports.

```text
Client (port 52738) ──► Request ──► Server (port 443)
Client (port 52738) ◄── Response ◄── Server (port 52738)
                                     ↑
                                     Ephemeral port!
                                     NACL must allow outbound
                                     on ports 1024-65535
```

If the NACL outbound rules don't allow the ephemeral port range (1024–65535), the response packets are dropped — even though the request was allowed inbound.

**Security Groups don't have this problem** because they are stateful (return traffic is auto-allowed).

---

# When to Use NACLs

| Scenario | Use NACL? | Why |
|----------|-----------|-----|
| Block a specific malicious IP | **Yes** | NACLs support deny rules. SGs cannot deny. |
| Subnet-level deny for compliance | **Yes** | Blanket deny at the subnet boundary |
| Defense-in-depth (layered security) | **Yes** | NACL = outer layer, SG = inner layer |
| Standard application tier security | **No** | SGs are sufficient and simpler |
| Instance-level traffic control | **No** | SGs are designed for this |

**In Practice**: Most architectures only use Security Groups. NACLs are used for specific deny rules (blocking IPs) or compliance requirements.

---

# Real-World Scenario

**Problem**: A malicious IP (`203.0.113.42`) is sending abusive requests to your web servers.

**Security Group**: Cannot block it — SGs only have allow rules.

**NACL Solution**:
```text
Rule # 50 | All Traffic | All | All | 203.0.113.42/32 | DENY
```
Add this rule with a **lower number** than the allow rules so it is evaluated first.

---

# Common Mistakes

- Forgetting ephemeral ports in NACL outbound rules — responses get silently dropped.
- Using NACLs for fine-grained per-instance rules. NACLs apply to the entire subnet — use SGs for per-instance control.
- Not understanding rule evaluation order in NACLs — a DENY at rule 100 blocks traffic even if rule 200 allows it.
- Overcomplicating architecture by using both NACLs and SGs when SGs alone would suffice.

---

# Key Takeaways

- Security Groups are stateful and instance-level. NACLs are stateless and subnet-level.
- SGs: allow-only, all rules evaluated. NACLs: allow + deny, evaluated in numbered order.
- NACLs require ephemeral port rules for return traffic (SGs handle this automatically).
- Use SGs for all standard traffic control. Use NACLs only for deny rules and compliance.
- The most common NACL use case is blocking a specific IP or CIDR range.

---
