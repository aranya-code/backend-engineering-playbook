# Security Groups and NACLs

Security Groups and Network ACLs (NACLs) are the two layers of network security within a VPC. Security Groups operate as stateful firewalls at the instance level, while NACLs operate as stateless firewalls at the subnet level. Together, they implement defense-in-depth network protection.

This is one of the most frequently tested topics in AWS certifications and interviews — understanding the differences and knowing when to use each is critical.

---

# Security Groups

## What are Security Groups?

Security Groups act as virtual firewalls attached to ENIs (Elastic Network Interfaces). They control inbound and outbound traffic at the **instance level**.

## Key Characteristics

- **Stateful** — if inbound traffic is allowed, the return traffic is automatically allowed (and vice versa)
- **Allow rules only** — you cannot create deny rules
- **All rules evaluated** — all rules are evaluated before deciding to allow traffic (no ordering)
- **Default behavior** — all inbound traffic denied, all outbound traffic allowed
- **Applied to ENIs** — an instance can have up to 5 security groups

## Security Group Rule Structure

```text
┌───────────┬──────────┬──────────┬───────────────┐
│ Direction │ Protocol │ Port     │ Source/Dest    │
├───────────┼──────────┼──────────┼───────────────┤
│ Inbound   │ TCP      │ 443      │ 0.0.0.0/0     │
│ Inbound   │ TCP      │ 8080     │ sg-alb-12345  │
│ Outbound  │ All      │ All      │ 0.0.0.0/0     │
└───────────┴──────────┴──────────┴───────────────┘
```

## Security Group Chaining

Reference other security groups as sources/destinations instead of CIDR ranges. This creates dynamic, maintainable rules.

```text
ALB Security Group (sg-alb)
├── Inbound: Port 443 from 0.0.0.0/0

App Security Group (sg-app)
├── Inbound: Port 8080 from sg-alb     ◄── Reference SG, not CIDR

DB Security Group (sg-db)
├── Inbound: Port 5432 from sg-app     ◄── Reference SG, not CIDR
```

Benefits:
- Rules automatically apply to new instances added to the referenced SG
- No need to update rules when IPs change
- Cleaner, more maintainable security model

---

# Network ACLs (NACLs)

## What are NACLs?

NACLs are stateless firewalls at the **subnet level**. They control inbound and outbound traffic for all resources within the subnet.

## Key Characteristics

- **Stateless** — return traffic must be explicitly allowed (both directions)
- **Allow AND deny rules** — you can block specific IPs or ranges
- **Rules evaluated in order** — lowest rule number wins, evaluation stops at first match
- **Default NACL** — allows all inbound and outbound traffic
- **Custom NACL** — denies all inbound and outbound traffic by default
- **One NACL per subnet** — a subnet can only be associated with one NACL

## NACL Rule Structure

```text
Inbound Rules:
┌──────┬──────────┬──────────┬───────────────┬────────┐
│ Rule │ Protocol │ Port     │ Source        │ Action │
├──────┼──────────┼──────────┼───────────────┼────────┤
│ 100  │ TCP      │ 443      │ 0.0.0.0/0    │ ALLOW  │
│ 200  │ TCP      │ 80       │ 0.0.0.0/0    │ ALLOW  │
│ 300  │ TCP      │ 22       │ 10.0.0.0/16  │ ALLOW  │
│ *    │ All      │ All      │ 0.0.0.0/0    │ DENY   │
└──────┴──────────┴──────────┴───────────────┴────────┘

Outbound Rules:
┌──────┬──────────┬──────────────┬───────────────┬────────┐
│ Rule │ Protocol │ Port         │ Destination   │ Action │
├──────┼──────────┼──────────────┼───────────────┼────────┤
│ 100  │ TCP      │ 1024-65535   │ 0.0.0.0/0    │ ALLOW  │
│ *    │ All      │ All          │ 0.0.0.0/0    │ DENY   │
└──────┴──────────┴──────────────┴───────────────┴────────┘
```

## Ephemeral Ports

Because NACLs are stateless, outbound rules must allow **ephemeral ports** (1024–65535) for return traffic.

```text
Client → Server:
  Inbound: Port 443 ALLOW

Server → Client (response):
  Outbound: Port 1024-65535 ALLOW  ◄── Required for response!
```

---

# Security Groups vs NACLs — Comparison

| Feature | Security Groups | NACLs |
|---------|----------------|-------|
| **Scope** | Instance (ENI) | Subnet |
| **Statefulness** | Stateful | Stateless |
| **Rule types** | Allow only | Allow and Deny |
| **Rule evaluation** | All rules (no order) | In order (first match wins) |
| **Default inbound** | Deny all | Allow all (default NACL) |
| **Default outbound** | Allow all | Allow all (default NACL) |
| **Return traffic** | Automatic | Must be explicitly allowed |
| **Applies to** | Only assigned instances | All instances in the subnet |
| **Rules per group** | 60 inbound + 60 outbound | 20 inbound + 20 outbound |
| **Multiple associations** | Up to 5 SGs per ENI | 1 NACL per subnet |

---

# Traffic Flow Through Both Layers

```text
Internet
    │
    ▼
┌─────────────────────┐
│   NACL (Subnet)     │  ◄── Evaluated first (stateless)
│   Inbound Rules     │
│   Rule 100: ALLOW   │
│   Rule *: DENY      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Security Group     │  ◄── Evaluated second (stateful)
│  Inbound Rules      │
│  Port 443: ALLOW    │
└──────────┬──────────┘
           │
           ▼
      EC2 Instance
           │
           ▼
┌─────────────────────┐
│  Security Group     │  ◄── Return traffic: automatic (stateful)
│  (No check needed)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   NACL (Subnet)     │  ◄── Return traffic: MUST be allowed (stateless)
│   Outbound Rules    │
│   Ephemeral ports   │
└─────────────────────┘
```

---

# When to Use Each

## Security Groups (Primary Control)

- **Always use** — every resource should have properly configured security groups
- Fine-grained, per-instance traffic control
- Reference other SGs for dynamic, maintainable rules
- Use SG chaining across tiers (ALB → App → DB)

## NACLs (Additional Guardrails)

- Block known malicious IP ranges at the subnet level
- Compliance requirement for an additional security layer
- Deny rules that cannot be expressed in security groups
- Subnet-level backstop in case security groups are misconfigured

---

# Best Practices

| Practice | Detail |
|----------|--------|
| Use SG chaining | Reference SGs, not CIDRs, for inter-tier rules |
| Separate SGs per tier | Web SG, App SG, DB SG — never share |
| Never open 22 to 0.0.0.0/0 | Use SSM Session Manager instead |
| Use descriptive names | `prod-web-alb-sg` not `sg-abc123` |
| Minimize outbound rules | Restrict outbound to known destinations when possible |
| Use NACLs sparingly | As additional guardrails, not primary control |
| Number NACL rules by 100s | Leave gaps (100, 200, 300) for easy insertion |

---

# Key Takeaways

- **Security Groups** are your primary traffic control — stateful, instance-level, allow-only.
- **NACLs** are additional subnet-level guardrails — stateless, support deny rules.
- Security Groups evaluate all rules; NACLs evaluate in order (first match wins).
- NACLs require explicit ephemeral port rules for return traffic.
- Always use SG chaining (reference other SGs) over CIDR-based rules.
- Traffic passes through NACL first, then Security Group on the way in.
- Both layers together implement defense-in-depth network security.

---
