# README

## Overview

This folder contains architecture-level documentation for designing, implementing, and operating secure AWS environments. It focuses on how security controls work together across identity, network boundaries, application workloads, encryption, audit logging, threat detection, and incident response.

The architecture guidance is intended for backend engineers and technical leads building production systems with AWS services such as EC2, Lambda, API Gateway, S3, RDS, IAM, AWS KMS, and CloudWatch.

The emphasis is on security boundaries, trust relationships, defense in depth, operational visibility, and practical decisions that reduce risk without introducing unnecessary complexity.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- AWS Security Architecture](./01-%20AWS%20Security%20Architecture.md) | Establishes security architecture principles, account boundaries, workload isolation, identity design, encryption, and secure service-to-service communication |
| 02 | [02- Defense in Depth](./02-%20Defense%20in%20Depth.md) | Explains layered security controls, failure containment, preventive and detective safeguards, and production implementation patterns |
| 03 | [03- Security Monitoring and Threat Detection Architecture](./03-%20Security%20Monitoring%20and%20Threat%20Detection%20Architecture.md) | Covers centralized audit logging, CloudTrail, GuardDuty, Security Hub, CloudWatch, AWS Config, event-driven detections, and incident-response workflows |

## Architecture Scope

The documents cover the following security architecture concerns.

| Area | Architectural objective | Relevant AWS services and controls |
|---|---|---|
| Account isolation | Reduce blast radius and separate administrative responsibilities | AWS Organizations, service control policies, dedicated security and log archive accounts |
| Identity and access | Ensure identities receive only the permissions required for their responsibilities | IAM roles, trust policies, IAM policies, AWS STS, workload identities |
| Network security | Minimize exposure and control communication paths | VPCs, subnets, security groups, network ACLs, VPC endpoints, AWS PrivateLink |
| Application protection | Protect public APIs and application entry points | API Gateway, AWS WAF, AWS Shield, application-level authentication and authorization |
| Data protection | Protect sensitive information throughout its lifecycle | AWS KMS, S3 encryption, EBS encryption, RDS encryption, TLS |
| Secret management | Avoid embedding credentials in application code and deployment artifacts | AWS Secrets Manager, Systems Manager Parameter Store, IAM-based access |
| Monitoring and detection | Identify suspicious activity and security configuration drift | CloudTrail, GuardDuty, Security Hub, CloudWatch, AWS Config |
| Incident response | Investigate, contain, remediate, and recover from security incidents | EventBridge, Lambda, centralized logs, restricted response roles, documented procedures |

## Recommended Reading Order

Follow the sequence below when learning or reviewing the architecture.

1. **AWS Security Architecture** — Understand the major security boundaries and how identity, network, data, and monitoring controls fit together.
2. **Defense in Depth** — Learn how multiple independent controls reduce the impact of individual control failures.
3. **Security Monitoring and Threat Detection Architecture** — Understand how security events become findings, alerts, investigations, and controlled response actions.

Read these architecture documents alongside the corresponding AWS security concept and operational documentation when implementing a particular service or control.

## Architecture Design Principles

### Least privilege by default

Use narrowly scoped IAM permissions, resource policies, and workload roles. Avoid shared credentials and broad administrative permissions for routine application execution.

### Explicit security boundaries

Separate workload execution, security administration, and audit-log storage according to the organization's risk and operational requirements. Treat account boundaries as one layer of protection rather than a substitute for correct authorization.

### Layered protection

Combine identity controls, network restrictions, application authorization, encryption, monitoring, and incident-response procedures. A control should not be assumed to compensate for every failure in another layer.

### Centralized visibility with controlled access

Centralize audit evidence and security findings while limiting who can modify logging configurations, delete evidence, or execute response actions.

### Secure automation

Use dedicated automation roles with bounded permissions, validation, idempotency, logging, and failure handling. Require human approval for high-impact actions when automated decisions cannot be made reliably.

### Continuous verification

Periodically test account and Region coverage, IAM trust relationships, encryption settings, network exposure, log delivery, alert routing, and incident-response procedures.

## Production Review Checklist

Use this checklist during architecture reviews and significant security changes.

- [ ] Account boundaries and administrative responsibilities are clearly defined.
- [ ] Workloads use short-lived credentials and least-privilege execution roles.
- [ ] Cross-account trust relationships are restricted and reviewed.
- [ ] Public network exposure is explicitly justified and minimized.
- [ ] Sensitive data is encrypted using appropriate key-management controls.
- [ ] Secrets are stored and rotated through approved secret-management mechanisms.
- [ ] Audit logging covers the required accounts, Regions, and event categories.
- [ ] Security findings have defined owners, priorities, and escalation paths.
- [ ] Incident-response permissions and automation are tested and appropriately restricted.
- [ ] Security exceptions have documented owners, rationale, and review dates.

## Key Takeaways

- AWS security architecture depends on coordinated identity, network, application, data-protection, and monitoring controls.
- Account separation and least privilege reduce blast radius but do not eliminate the need for explicit authorization and continuous review.
- Centralized audit logging and threat detection are effective only when coverage, retention, alert delivery, and ownership are verified.
- Automated response should be narrowly scoped, auditable, idempotent, and designed to preserve evidence while limiting operational disruption.
- Treat security architecture as an ongoing operational responsibility, validated through configuration reviews, detection tests, and incident-response exercises.