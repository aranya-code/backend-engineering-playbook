# IAM Roles

Temporary, assumable identities — how they work, how EC2 and other services use them, and cross-account access patterns.

---

# Topics Covered

| # | Topic | Key Concepts |
|---|-------|-------------|
| 01 | [IAM Roles](./01-%20IAM%20Roles.md) | Trust policy vs permission policy, why roles beat long-term credentials |
| 02 | [EC2 Roles](./02-%20EC2%20Roles.md) | EC2 instance roles, Lambda execution roles, CloudFormation service roles |
| 03 | [Assume Role](./03-%20Assume%20Role.md) | AssumeRole flow, trust policy principals, External ID safeguard |
| 04 | [Instance Profiles](./04-%20Instance%20Profiles.md) | The container object that attaches a role to an EC2 instance |
| 05 | [Cross-Account Roles](./05-%20Cross-Account%20Roles.md) | Full setup pattern for one account assuming a role in another |
| 06 | [Service-Linked Roles](./06-%20Service-Linked%20Roles.md) | Predefined AWS-controlled roles (e.g., `AWSServiceRoleForAutoScaling`) |

---

# How Roles Work

```text
Caller (User / Service / Another Account)
          │
          ▼
   sts:AssumeRole
          │
          ▼
┌─────────────────────────┐
│       IAM Role          │
│  ┌───────────────────┐  │
│  │   Trust Policy    │  │  ← WHO can assume this role?
│  │   (Principal)     │  │
│  └───────────────────┘  │
│  ┌───────────────────┐  │
│  │ Permission Policy │  │  ← WHAT can this role do?
│  │ (Actions/Resources)│  │
│  └───────────────────┘  │
└─────────────────────────┘
          │
          ▼
   Temporary Credentials
   (AccessKeyId, SecretAccessKey, SessionToken)
   Expires in 1–12 hours
```

---

# Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [IAM Module](../README.md) |
| ⬅️ Previous | [Policies](../01-%20Policies/) |
| ➡️ Next | [Security](../03-%20Security/) |

---

*Part of the [Backend Engineering Playbook](../../../../) — Aranya Majumdar*
