# Security Groups

# What Are Security Groups?

Security Groups are stateful virtual firewalls that control inbound and outbound traffic at the Elastic Network Interface (ENI) level. They are the primary network security mechanism for EC2 instances and most AWS resources within a VPC.

---

# Core Characteristics

| Characteristic | Detail |
|---------------|--------|
| Scope | Attached to ENI (instance-level), scoped to VPC |
| Statefulness | **Stateful** — if inbound is allowed, the response is automatically allowed outbound |
| Rule Type | **Allow rules only** — you cannot create deny rules |
| Default Inbound | All inbound traffic **denied** by default |
| Default Outbound | All outbound traffic **allowed** by default |
| Evaluation | All rules evaluated together (not in order). If any rule matches, traffic is allowed |
| Operates At | Outside the OS kernel — blocked traffic never reaches the instance |

---

# Security Group Chaining

The most important production pattern: reference Security Group IDs instead of CIDR blocks for internal communication.

```text
Internet
    │
    ▼
┌────────────────────────────────────────────────────────────┐
│ VPC                                                         │
│                                                             │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────┐ │
│  │  ALB          │      │  App Server  │      │   RDS    │ │
│  │              │      │              │      │          │ │
│  │ ALB-SG       │      │ App-SG       │      │ DB-SG    │ │
│  │ Inbound:     │      │ Inbound:     │      │ Inbound: │ │
│  │  443 from    │──────►  8080 from   │──────►  5432    │ │
│  │  0.0.0.0/0   │      │  ALB-SG      │      │  from    │ │
│  │              │      │  (SG ref!)   │      │  App-SG  │ │
│  └──────────────┘      └──────────────┘      └──────────┘ │
│                                                             │
└────────────────────────────────────────────────────────────┘

Key: App-SG allows port 8080 from ALB-SG (not from a CIDR).
     DB-SG allows port 5432 from App-SG (not from a CIDR).

Benefits:
  - If ALB or App instances scale (new IPs), rules still work automatically.
  - No need to update SG rules when instances are added/removed.
  - Tighter security — only traffic from the correct tier is allowed.
```

---

# Self-Referencing Security Groups

Allow instances within the same Security Group to communicate with each other:

```text
SG: Cluster-SG
  Inbound Rule: All TCP from Cluster-SG (self-reference)

EC2 (10.0.1.10) ◄──────► EC2 (10.0.1.11)
     │                        │
     └── Both in Cluster-SG ──┘

Use case: Elasticsearch clusters, Kafka brokers, Redis clusters
```

---

# Limits

| Limit | Default | Max (with request) |
|-------|---------|-------------------|
| SGs per ENI | 5 | 16 |
| Inbound rules per SG | 60 | 200 |
| Outbound rules per SG | 60 | 200 |

**Effective rules per instance** = SGs per ENI × Rules per SG = 5 × 60 = 300 rules evaluated per packet.

---

# Troubleshooting Connectivity

If you cannot connect to an EC2 instance, check in this order:

```text
1. Security Group ── Is the correct port/protocol allowed from your source?
2. NACL ──────────── Is the subnet NACL allowing the traffic (+ ephemeral ports)?
3. Route Table ───── Does a route exist to the destination?
4. Internet Gateway ─ Is an IGW attached (for public internet access)?
5. Elastic IP / Public IP ── Does the instance have a public IP?
6. OS Firewall ───── Is iptables/firewalld blocking inside the OS?
```

---

# Common Mistakes

- Opening port 22 (SSH) to `0.0.0.0/0` in production. Restrict to specific admin IPs or use SSM.
- Using CIDR blocks for internal SG rules instead of SG references. CIDR rules break when instances scale.
- Forgetting that SGs are **allow-only** — you cannot block a specific IP with a Security Group (use NACLs for deny rules).
- Not creating separate SGs per tier (Web-SG, App-SG, DB-SG). Using one SG for everything defeats defense-in-depth.
- Modifying the default Security Group — create custom SGs instead and leave the default untouched.

---

# Key Takeaways

- Security Groups are stateful, allow-only firewalls at the ENI level.
- Use SG chaining (reference SG IDs, not CIDRs) for internal tier communication.
- Default behavior: all inbound denied, all outbound allowed.
- SGs operate outside the OS — blocked traffic never reaches the instance kernel.
- For deny rules, use NACLs (subnet-level, stateless).
- Always create separate SGs per application tier (ALB, App, DB, Bastion).

---
