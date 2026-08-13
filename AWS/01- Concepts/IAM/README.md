# AWS IAM (Identity and Access Management)

A comprehensive, production-focused playbook on AWS IAM — the service that controls authentication and authorization for every AWS API call. This module covers IAM fundamentals, policy structure and evaluation, roles and delegation, security hardening, monitoring, troubleshooting, and senior-level interview preparation.

---

# What You Will Learn

By completing this module, you will understand:

- IAM Architecture and Core Entities
- Users, Groups, and Roles (when to use each)
- Policy Structure, Evaluation Logic, and Guardrails
- IAM Roles, AssumeRole, and Cross-Account Access
- Instance Profiles and Service-Linked Roles
- Security Hardening (MFA, Least Privilege, Root Account Lockdown)
- Credential Rotation and Access Analyzer
- Privilege Escalation Paths and Prevention
- Monitoring (Access Advisor, Credentials Report)
- Troubleshooting Access Denied and AssumeRole Errors
- Senior-Level Interview Preparation

---

# Module Structure

```text
IAM-upgraded/
│
├── README.md                          ← You are here
├── 01- IAM Basics.md                  Core entities, global service, root account
├── 02- Users vs Groups vs Roles.md    When to use each, why groups can't be nested
│
├── 01- Policies/                      Policy structure and evaluation (7 files)
│   ├── README.md
│   ├── 01- Policy Basics.md
│   ├── 02- IAM Policy Structure.md
│   ├── 03- Inline vs Managed Policies.md
│   ├── 04- Policy Examples.md
│   ├── 05- Policy Evaluation Logic.md
│   ├── 06- Permission Boundaries and SCPs.md
│   └── 07- Attribute-Based Access Control (ABAC).md
│
├── 02- Roles/                         Temporary identities and delegation (6 files)
│   ├── README.md
│   ├── 01- IAM Roles.md
│   ├── 02- EC2 Roles.md
│   ├── 03- Assume Role.md
│   ├── 04- Instance Profiles.md
│   ├── 05- Cross-Account Roles.md
│   └── 06- Service-Linked Roles.md
│
├── 03- Security/                      Hardening and threat prevention (6 files)
│   ├── README.md
│   ├── 01- MFA.md
│   ├── 02- Root Account Best Practices.md
│   ├── 03- Least Privilege.md
│   ├── 04- Credential Rotation.md
│   ├── 05- IAM Access Analyzer.md
│   └── 06- IAM Privilege Escalation Paths.md
│
├── 04- Monitoring/                    Usage tracking and audit (2 files)
│   ├── README.md
│   ├── 01- IAM Access Advisor.md
│   └── 02- IAM Credentials Report.md
│
├── 05- Troubleshooting/              Debugging permission failures (3 files)
│   ├── README.md
│   ├── 01- Access Denied.md
│   ├── 02- STS AssumeRole Errors.md
│   └── 03- Policy Simulator and Debugging Tools.md
│
└── 06- Interview/                     Preparation and quick revision (2 files)
    ├── README.md
    ├── 01- IAM Interview Questions.md
    └── 02- Quick Revision.md
```

---

# Module Directory

| # | Directory | Files | Description |
|---|-----------|-------|-------------|
| — | Root Files | 2 | IAM Basics, Users vs Groups vs Roles |
| 01 | [Policies](./01-%20Policies/) | 7 | Policy structure, evaluation logic, ABAC, permission boundaries, SCPs |
| 02 | [Roles](./02-%20Roles/) | 6 | Trust policies, instance profiles, cross-account access, service-linked roles |
| 03 | [Security](./03-%20Security/) | 6 | MFA, root lockdown, least privilege, credential rotation, privilege escalation |
| 04 | [Monitoring](./04-%20Monitoring/) | 2 | Access Advisor (per-identity), Credentials Report (account-wide) |
| 05 | [Troubleshooting](./05-%20Troubleshooting/) | 3 | Access Denied debugging, AssumeRole errors, Policy Simulator |
| 06 | [Interview](./06-%20Interview/) | 2 | 15 Q&A across all levels, quick revision cheat sheet |

---

# IAM Architecture Overview

```text
AWS Account
│
├── Root Account (unrestricted, never use for daily operations)
│
├── IAM Users ──► Long-term credentials (password, access keys)
│   └── Grouped into IAM Groups (permissions inherited)
│
├── IAM Roles ──► Temporary credentials (STS AssumeRole)
│   ├── EC2 Instance Roles (via Instance Profiles)
│   ├── Lambda Execution Roles
│   ├── Cross-Account Roles
│   └── Service-Linked Roles (AWS-managed)
│
├── IAM Policies ──► JSON documents defining permissions
│   ├── Identity-Based Policies (attached to users, groups, roles)
│   ├── Resource-Based Policies (attached to S3, SQS, Lambda, etc.)
│   ├── Permission Boundaries (max permission cap)
│   └── Service Control Policies (Organizations-level guardrails)
│
└── Policy Evaluation ──► Explicit Deny → SCP → Resource Policy → 
                          Permission Boundary → Identity Policy → Allow/Deny
```

---

# Learning Path

```text
Phase 1: Fundamentals
  IAM Basics → Users vs Groups vs Roles

Phase 2: Policies (How Permissions Work)
  Policy Basics → Policy Structure → Inline vs Managed →
  Policy Examples → Evaluation Logic → Boundaries & SCPs → ABAC

Phase 3: Roles (How Delegation Works)
  IAM Roles → EC2 Roles → AssumeRole →
  Instance Profiles → Cross-Account → Service-Linked Roles

Phase 4: Security (Hardening)
  MFA → Root Account → Least Privilege →
  Credential Rotation → Access Analyzer → Privilege Escalation Paths

Phase 5: Operations
  Access Advisor → Credentials Report →
  Access Denied Debugging → AssumeRole Errors → Policy Simulator

Phase 6: Interview Preparation
  Interview Questions → Quick Revision
```

---

# Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [AWS Concepts](../README.md) |

---

> **Part of the [Backend Engineering Playbook](../../../) — a structured learning resource for backend engineers.**

*Created by Aranya Majumdar*
