# Compliance and Auditing

AWS provides a comprehensive set of services and programs for meeting regulatory compliance requirements and maintaining continuous audit trails. Compliance in the cloud is a shared responsibility — AWS maintains compliance certifications for the infrastructure, while customers must ensure their workloads comply with applicable regulations.

Understanding compliance services is essential for organizations in regulated industries (finance, healthcare, government) and for passing AWS certification exams.

---

# AWS Compliance Programs

AWS maintains compliance certifications and attestations for the underlying infrastructure.

| Program | Description | Industries |
|---------|-------------|------------|
| **SOC 1/2/3** | Service Organization Controls (audit reports) | Financial, all industries |
| **ISO 27001** | Information security management | All industries |
| **ISO 27017** | Cloud-specific security controls | All industries |
| **ISO 27018** | PII protection in public cloud | All industries |
| **PCI DSS Level 1** | Payment card industry data security | E-commerce, financial |
| **HIPAA** | Health information privacy and security | Healthcare |
| **FedRAMP** | US federal government cloud security | Government |
| **GDPR** | EU data protection regulation | Any business handling EU data |
| **SOX** | Financial reporting controls | Publicly traded companies |

---

## AWS Artifact

AWS Artifact provides on-demand access to AWS compliance reports and agreements.

- Download SOC reports, ISO certificates, PCI attestations
- Review and accept agreements (BAA for HIPAA, DPA for GDPR)
- No cost
- Available in the AWS Console

---

# AWS Config

AWS Config continuously monitors and records AWS resource configurations and evaluates them against desired compliance rules.

## How Config Works

```text
AWS Resource Change
       │
       ▼
  AWS Config
  (Records Configuration)
       │
       ├──► Configuration History
       │    (Timeline of changes)
       │
       ├──► Config Rules
       │    (Compliance evaluation)
       │
       └──► Remediation Actions
            (Auto-fix non-compliant resources)
```

## Config Rules

Config Rules evaluate whether resource configurations comply with your policies.

### AWS Managed Rules (200+)

| Rule | What It Checks |
|------|---------------|
| `s3-bucket-public-read-prohibited` | S3 buckets are not publicly readable |
| `encrypted-volumes` | EBS volumes are encrypted |
| `rds-instance-public-access-check` | RDS instances are not publicly accessible |
| `iam-root-access-key-check` | Root account has no access keys |
| `multi-region-cloudtrail-enabled` | CloudTrail is enabled in all regions |
| `vpc-flow-logs-enabled` | VPC Flow Logs are enabled |
| `restricted-ssh` | SSH (port 22) is not open to 0.0.0.0/0 |

### Custom Rules

- Write custom compliance logic using Lambda functions
- Evaluate any resource property
- Trigger on configuration changes or on a schedule

## Conformance Packs

Conformance Packs are collections of Config Rules and remediation actions packaged together for a specific compliance framework.

| Pack | Rules Included |
|------|---------------|
| **CIS AWS Foundations** | 40+ rules for CIS benchmark |
| **PCI DSS** | 30+ rules for payment card compliance |
| **HIPAA** | 50+ rules for healthcare compliance |
| **NIST 800-53** | 60+ rules for government compliance |
| **AWS Best Practices** | 40+ rules for operational best practices |

## Automatic Remediation

Config can automatically fix non-compliant resources using SSM Automation documents.

```text
Config Rule Evaluation
       │
   NON_COMPLIANT
       │
       ▼
  Remediation Action
  (SSM Automation)
       │
       ▼
  Resource Fixed
  (Re-evaluated as COMPLIANT)
```

Example: If an S3 bucket is detected without encryption, Config can automatically enable default SSE-S3 encryption.

---

# AWS CloudTrail for Auditing

CloudTrail is the primary auditing service in AWS, recording every supported API call.

## Audit Capabilities

| Capability | Description |
|-----------|-------------|
| **Who** | IAM user, role, or service that made the call |
| **What** | API action performed (e.g., `RunInstances`, `DeleteBucket`) |
| **When** | Timestamp of the event |
| **Where** | AWS Region and source IP address |
| **How** | Request parameters and response elements |

## CloudTrail + Config Together

```text
CloudTrail                    Config
(WHO changed WHAT)           (IS it COMPLIANT?)

"User X changed             "Security group sg-abc
 security group sg-abc        now allows port 22
 at 2026-07-07 15:00"        from 0.0.0.0/0"
                              → NON_COMPLIANT
```

CloudTrail answers **who did it**. Config answers **is it compliant**.

---

# AWS Audit Manager

AWS Audit Manager automates evidence collection for audits, mapping AWS activity to compliance frameworks.

- Continuously collects evidence from CloudTrail, Config, and Security Hub
- Maps evidence to compliance control frameworks
- Generates audit-ready reports
- Supports SOC 2, PCI DSS, HIPAA, GDPR, and custom frameworks
- Reduces manual audit preparation effort

```text
Evidence Sources              Audit Manager              Output

CloudTrail Events ──────►     │                    Audit Reports
Config Compliance ──────►  Framework  ──────►     Evidence Folders
Security Hub Findings ──►  Assessment             Control Mapping
Manual Evidence ────────►     │                    Delegation
```

---

# Continuous Compliance Architecture

```text
┌─────────────────────────────────────────────────┐
│              Compliance Architecture             │
│                                                  │
│  ┌──────────────┐   ┌──────────────┐            │
│  │  CloudTrail  │   │  AWS Config  │            │
│  │  (API Audit) │   │  (Compliance │            │
│  │              │   │   Rules)     │            │
│  └──────┬───────┘   └──────┬───────┘            │
│         │                  │                     │
│         └────────┬─────────┘                     │
│                  │                               │
│                  ▼                               │
│         ┌────────────────┐                       │
│         │  Security Hub  │                       │
│         │  (Aggregation) │                       │
│         └───────┬────────┘                       │
│                 │                                │
│         ┌───────┴────────┐                       │
│         │                │                       │
│         ▼                ▼                       │
│  ┌─────────────┐  ┌─────────────┐               │
│  │Audit Manager│  │ EventBridge │               │
│  │(Reporting)  │  │ + Lambda    │               │
│  │             │  │(Auto-Remediate)│             │
│  └─────────────┘  └─────────────┘               │
└─────────────────────────────────────────────────┘
```

---

# Key Takeaways

- AWS maintains compliance certifications for infrastructure; customers must comply for their workloads.
- **AWS Config** continuously evaluates resource configurations against compliance rules.
- **CloudTrail** provides the audit trail of who did what and when.
- **Security Hub** aggregates compliance findings with security scores.
- **Audit Manager** automates evidence collection and audit reporting.
- Use **Conformance Packs** to deploy pre-built rule sets for PCI DSS, HIPAA, CIS, and NIST.
- Automatic remediation via Config + SSM closes compliance gaps without manual intervention.
- CloudTrail + Config together answer both "who changed it" and "is it compliant."

---

# Interview Questions

### Q: What is the difference between CloudTrail and Config?

CloudTrail records API activity (who did what, when). Config records resource configurations and evaluates compliance (is it compliant now).

### Q: What is a Conformance Pack?

A collection of Config Rules and remediation actions packaged together for a specific compliance framework (e.g., PCI DSS, HIPAA).

### Q: How does Config auto-remediation work?

When a Config Rule evaluates a resource as NON_COMPLIANT, it can trigger an SSM Automation document to automatically fix the configuration.

### Q: What is AWS Artifact?

A service that provides on-demand access to AWS compliance reports (SOC, ISO, PCI) and agreements (BAA, DPA).

---
