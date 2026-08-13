# IAM Security

Hardening IAM itself — MFA, root account practices, least privilege, credential rotation, and automated detection of unintended access and privilege escalation.

---

# Topics Covered

| # | Topic | Key Concepts |
|---|-------|-------------|
| 01 | [MFA](./01-%20MFA.md) | Device types (Virtual, Hardware, U2F), enforcing via policy condition, why SMS is discouraged |
| 02 | [Root Account Best Practices](./02-%20Root%20Account%20Best%20Practices.md) | Why root is unrestricted by IAM, lockdown procedures, what root is required for |
| 03 | [Least Privilege](./03-%20Least%20Privilege.md) | Why it's harder than it sounds, practical techniques for achieving it |
| 04 | [Credential Rotation](./04-%20Credential%20Rotation.md) | What to rotate, two-key rotation process, why long-term credentials are shrinking |
| 05 | [IAM Access Analyzer](./05-%20IAM%20Access%20Analyzer.md) | Finding unintended external access, generating least-privilege policies from usage |
| 06 | [Privilege Escalation Paths](./06-%20IAM%20Privilege%20Escalation%20Paths.md) | Permission combos (PassRole + CreateFunction) that let identities escalate access |

---

# Security Hardening Checklist

```text
Priority 1 (Day One):
  ✓ Enable MFA on root account (hardware key preferred)
  ✓ Create IAM admin user, stop using root
  ✓ Enable CloudTrail in all regions
  ✓ Enable IAM Access Analyzer

Priority 2 (First Week):
  ✓ Remove all root access keys
  ✓ Enforce MFA via IAM policy conditions
  ✓ Apply least-privilege policies (start with AWS managed, refine with Access Advisor)
  ✓ Set password policy (14+ chars, rotation)

Priority 3 (Ongoing):
  ✓ Review Credentials Report monthly (find unused keys/passwords)
  ✓ Review Access Advisor quarterly (revoke unused permissions)
  ✓ Audit for privilege escalation paths
  ✓ Rotate long-term credentials (or eliminate them with roles)
```

---

# Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [IAM Module](../README.md) |
| ⬅️ Previous | [Roles](../02-%20Roles/) |
| ➡️ Next | [Monitoring](../04-%20Monitoring/) |

---

*Part of the [Backend Engineering Playbook](../../../../) — Aranya Majumdar*
