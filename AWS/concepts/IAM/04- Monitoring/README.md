# IAM Monitoring

Tools for understanding what IAM identities actually use, and the credential hygiene of every user in the account.

---

# Topics Covered

| # | Topic | Key Concepts |
|---|-------|-------------|
| 01 | [IAM Access Advisor](./01-%20IAM%20Access%20Advisor.md) | Per-identity view: what services are granted vs what's actually been used, last-accessed timestamps |
| 02 | [IAM Credentials Report](./02-%20IAM%20Credentials%20Report.md) | Account-wide CSV of every user's password age, access key status, MFA status, last login |

---

# Monitoring vs Security Tools

```text
┌──────────────────────────┐     ┌──────────────────────────┐
│   Monitoring Tools       │     │   Security Tools         │
│   (Usage Tracking)       │     │   (Threat Detection)     │
│                          │     │                          │
│  Access Advisor          │     │  IAM Access Analyzer     │
│  → What did this user    │     │  → Are resources shared  │
│    actually access?      │     │    outside the account?  │
│                          │     │                          │
│  Credentials Report      │     │  Privilege Escalation    │
│  → Are credentials old,  │     │  → Can this identity     │
│    unused, or missing MFA│     │    grant itself more     │
│                          │     │    access?               │
└──────────────────────────┘     └──────────────────────────┘
```

---

# Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [IAM Module](../README.md) |
| ⬅️ Previous | [Security](../03-%20Security/) |
| ➡️ Next | [Troubleshooting](../05-%20Troubleshooting/) |

---

*Part of the [Backend Engineering Playbook](../../../../) — Aranya Majumdar*
