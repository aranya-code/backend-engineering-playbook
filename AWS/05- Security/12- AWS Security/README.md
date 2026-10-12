# README

## Overview

This directory contains the AWS Security engineering reference for designing, implementing, operating, and troubleshooting secure AWS environments. It focuses on security controls that protect backend applications, APIs, data stores, workloads, deployment pipelines, and cloud infrastructure.

The documentation progresses from foundational security concepts to identity and access management, encryption, network security, threat detection, secure architecture, operational workflows, troubleshooting, and senior-level interview preparation.

AWS security is implemented through multiple complementary controls rather than a single service. Identity policies determine which actions principals can perform, network controls restrict connectivity, encryption protects data, application controls validate requests, and monitoring services provide evidence of suspicious activity.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- Security Fundamentals and Threat Modeling](./01-%20Security%20Fundamentals%20and%20Threat%20Modeling.md) | Shared responsibility, defense in depth, least privilege, zero trust, and threat modeling fundamentals |
| 02 | [02- IAM and Access Control](./02-%20IAM%20and%20Access%20Control.md) | IAM principals, policies, trust relationships, STS, temporary credentials, and policy evaluation |
| 03 | [03- API Authentication and Signature Version 4](./03-%20API%20Authentication%20and%20Signature%20Version%204.md) | AWS Signature Version 4 signing, signed requests, credential scope, and common authentication failures |
| 04 | [04- Encryption at Rest and In Transit](./04-%20Encryption%20at%20Rest%20and%20In%20Transit.md) | TLS, encryption at rest, service-level encryption, and data protection patterns |
| 05 | [05- AWS KMS and Cryptographic Key Management](./05-%20AWS%20KMS%20and%20Cryptographic%20Key%20Management.md) | KMS key types, key policies, grants, rotation, envelope encryption, and cross-account key sharing |
| 06 | [06- Secrets Manager and Parameter Store](./06-%20Secrets%20Manager%20and%20Parameter%20Store.md) | AWS Secrets Manager, Systems Manager Parameter Store, secret rotation, caching, and secure application integration |
| 07 | [07- VPC Security and Network Access Controls](./07-%20VPC%20Security%20and%20Network%20Access%20Controls.md) | VPC security boundaries, security groups, network ACLs, VPC endpoints, and private connectivity |
| 08 | [08- AWS WAF and Shield](./08-%20AWS%20WAF%20and%20Shield.md) | AWS WAF rules, managed rule groups, AWS Shield, DDoS architecture, and application protection |
| 09 | [09- Threat Detection with GuardDuty and Security Hub](./09-%20Threat%20Detection%20with%20GuardDuty%20and%20Security%20Hub.md) | GuardDuty threat detection, Security Hub findings aggregation, compliance standards, and automated remediation |
| 10 | [10- Compliance and Security Auditing](./10-%20Compliance%20and%20Security%20Auditing.md) | CloudTrail, AWS Config, compliance monitoring, audit evidence, and continuous compliance evaluation |
| 11 | [11- Security Hardening and Best Practices](./11-%20Security%20Hardening%20and%20Best%20Practices.md) | Security hardening checklists, IAM best practices, network controls, encryption requirements, and monitoring |

### Scope

The reference covers:

- **Security fundamentals:** Shared Responsibility Model, defense in depth, least privilege, zero trust, threat modeling, and security boundaries.
- **Identity and access management:** IAM users, groups, roles, policies, STS, temporary credentials, cross-account access, and policy evaluation.
- **Request authentication:** AWS Signature Version 4 (SigV4), signed requests, credential scope, and common authentication failures.
- **Cryptographic controls:** AWS KMS, envelope encryption, key policies, grants, rotation, TLS, and encryption at rest.
- **Secrets management:** AWS Secrets Manager, Systems Manager Parameter Store, secret rotation, caching, and secure Python application integration.
- **Network and application protection:** VPC security boundaries, security groups, network ACLs, VPC endpoints, PrivateLink, AWS WAF, and AWS Shield.
- **Security monitoring:** CloudTrail, GuardDuty, Security Hub, AWS Config, CloudWatch, findings management, and centralized audit evidence.
- **Production security architecture:** Multi-account environments, workload isolation, centralized identity, secure APIs, and incident containment.
- **Operations and troubleshooting:** AWS CLI inspection workflows, access-denied investigations, KMS failures, secrets retrieval, network misconfigurations, and incident response.
- **Engineering practice:** Security checklists, practical exercises, backend-oriented examples, architecture trade-offs, and interview preparation.

## Documentation Structure

The documentation is organized by security responsibility so that foundational concepts, implementation details, operational procedures, and troubleshooting guidance can evolve independently.

The following table describes the intended navigation areas. Add or update individual links to match the Markdown files present in this directory.

| Area | Coverage | Primary use |
|---|---|---|
| Security Fundamentals | Shared responsibility, security boundaries, threat modeling, and defense in depth | Establish the security model and baseline controls |
| Identity and Access Management | IAM entities, policies, trust relationships, STS, and policy evaluation | Design and troubleshoot authentication and authorization |
| Request Authentication | SigV4 signing, temporary credentials, and signed API requests | Diagnose AWS API authentication failures |
| Encryption and Key Management | KMS, envelope encryption, TLS, key policies, and data protection | Protect data and govern cryptographic access |
| Secrets Management | Secrets Manager, Parameter Store, rotation, and application retrieval | Secure application configuration and credentials |
| Network Security | VPC controls, private connectivity, security groups, and network ACLs | Reduce network exposure and isolate workloads |
| Application Protection | AWS WAF, AWS Shield, and API security controls | Protect public-facing applications and APIs |
| Security Monitoring | CloudTrail, GuardDuty, Security Hub, AWS Config, and CloudWatch | Detect threats, audit activity, and investigate findings |
| Security Architecture | Multi-account security, centralized logging, workload isolation, and incident containment | Design production-ready security boundaries |
| Security Operations | Reviews, verification procedures, incident response, and security posture checks | Operate security controls consistently |
| AWS Security CLI | Read-only inspection, access analysis, findings retrieval, and controlled remediation | Investigate and verify security configurations |
| Troubleshooting | IAM, STS, SigV4, KMS, secrets, networking, WAF, and audit failures | Isolate failures using evidence rather than broad permissions |
| Interview Preparation | Core concepts, architecture scenarios, troubleshooting, and senior-level reasoning | Prepare for practical cloud security discussions |

## How to Use This Reference

### For learning

Start with security fundamentals before studying individual AWS services. Understand the difference between authentication, authorization, network reachability, request signing, encryption, and auditing. These controls solve different problems and should not be treated as interchangeable.

Proceed to IAM and STS before working through SigV4, KMS, and secrets management. Study network controls and application protection before reviewing security monitoring and incident response.

### For implementation

Use the relevant concept and architecture documentation before introducing a security control into a production system. Review the following questions during design:

- Which principal performs the operation, and how does it obtain its credentials?
- Which identity-based, resource-based, organizational, and session policies govern access?
- Which network paths are permitted, and can the workload use private connectivity?
- Where is sensitive data stored, and which KMS key or encryption mechanism protects it?
- How are application secrets delivered, rotated, cached, and revoked?
- Which audit events and security findings will be available during an incident?
- How will the team validate the configuration, detect regressions, and recover from failure?

### For troubleshooting

Investigate security failures systematically rather than granting broader permissions to make an error disappear.

1. Verify the active AWS identity and account.
2. Confirm the target resource, region, ARN, and requested operation.
3. Inspect identity policies, resource policies, trust policies, permissions boundaries, session policies, and applicable organization policies.
4. Check credential expiration, session tokens, request signing, and clock synchronization where relevant.
5. Inspect KMS authorization, network reachability, service configuration, and resource-specific restrictions.
6. Use CloudTrail, service logs, and security findings to establish what happened.
7. Apply the narrowest corrective change and verify the intended access path.

Not every denied request produces an immediately available or equally detailed diagnostic event. Account for service-specific logging behavior, event delivery delays, and the permissions required to inspect the evidence.

## Core Security Principles

| Principle | Engineering application |
|---|---|
| Least privilege | Grant only the actions and resources required by each workload or operator. |
| Short-lived credentials | Prefer IAM roles and temporary credentials over long-lived access keys. |
| Defense in depth | Combine identity, network, application, cryptographic, and detective controls. |
| Secure defaults | Disable unnecessary public access, avoid broad inbound rules, and require encryption where appropriate. |
| Separation of duties | Separate deployment, administration, audit, and security-response responsibilities where practical. |
| Centralized visibility | Aggregate audit evidence and security findings across relevant accounts and regions. |
| Continuous verification | Validate policies, network exposure, encryption, logging, and configuration drift regularly. |
| Evidence-driven response | Preserve logs and relevant metadata before making changes that could destroy investigation evidence. |

## Production Engineering Guidance

### Identity and access

- Use workload roles for EC2, Lambda, and other AWS-integrated compute services where supported.
- Use federation and centralized identity for human access instead of distributing long-lived IAM user credentials.
- Restrict role assumption through trust policies and apply least privilege to the resulting session.
- Review resource-based policies, permissions boundaries, service control policies, and other applicable policy constraints together.
- Use separate deployment identities with narrowly scoped permissions for CI/CD pipelines.
- Require MFA and stronger controls for privileged human access.

### Data protection

- Require TLS for sensitive data in transit and use service-supported encryption at rest.
- Define KMS key ownership, key policies, grants, rotation, recovery, and deletion safeguards before production deployment.
- Keep application credentials in an appropriate secrets-management service rather than source code or committed configuration.
- Treat secret rotation as an application lifecycle concern: clients, caches, connection pools, and dependent services must handle credential changes safely.
- Restrict access to secret values and encryption keys independently where the architecture supports it.

### Network and application protection

- Minimize public exposure and prefer private service connectivity where appropriate.
- Treat security groups, network ACLs, VPC endpoints, and AWS PrivateLink as complementary network controls.
- Apply authentication, authorization, input validation, and rate limiting at the appropriate application or API layer.
- Use AWS WAF and AWS Shield according to the application's exposure and threat model.
- Do not assume that private network placement alone establishes user or service authorization.

### Monitoring and incident response

- Enable and protect CloudTrail logging for the required accounts and regions.
- Centralize security findings and audit evidence according to organizational requirements.
- Use GuardDuty, Security Hub, AWS Config, and CloudWatch for their respective detection, aggregation, configuration assessment, and operational monitoring capabilities.
- Define response procedures for leaked credentials, suspicious API calls, unexpected public exposure, and KMS access failures.
- Test incident-response permissions, evidence access, credential revocation, and recovery procedures before an actual incident.
- Account for detection latency, log retention, service quotas, and the cost of centralized logging.

## Recommended AWS CLI Practices

Use the AWS CLI to inspect the current security context and gather evidence before changing controls. The examples below use placeholders and are intended for read-only verification unless explicitly stated otherwise.

Verify the active identity:

```bash
aws sts get-caller-identity
```

Inspect an IAM role and its trust policy:

```bash
aws iam get-role \
  --role-name <ROLE_NAME>
```

List policies attached directly to a role:

```bash
aws iam list-attached-role-policies \
  --role-name <ROLE_NAME>
```

Inspect an S3 bucket's public-access-block configuration:

```bash
aws s3api get-public-access-block \
  --bucket <BUCKET_NAME>
```

Inspect a KMS key:

```bash
aws kms describe-key \
  --key-id <KEY_ID> \
  --region <AWS_REGION>
```

Inspect secret metadata without retrieving the secret value:

```bash
aws secretsmanager describe-secret \
  --secret-id <SECRET_ID> \
  --region <AWS_REGION>
```

Review recent CloudTrail management events:

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRole \
  --start-time <START_TIME> \
  --end-time <END_TIME> \
  --region <AWS_REGION>
```

These commands require suitable read permissions. Successful inspection does not prove that a workload can perform the target operation: the effective authorization decision may depend on additional policies, service-specific controls, resource conditions, and runtime credentials.

Prefer scoped inspection commands and explicit regions during investigations. Treat command output as potentially sensitive, particularly when it contains resource identifiers, account metadata, policy documents, or configuration details. Do not paste credentials, secret values, session tokens, or unredacted sensitive evidence into shared logs or tickets.

## Maintenance and Contribution Standards

Keep each document focused on one security responsibility. Avoid duplicating detailed implementation steps across concept, architecture, CLI, operations, troubleshooting, and interview documents. Link related material when a concept is already explained elsewhere.

When updating this directory:

- Preserve existing terminology and useful examples.
- Use numbered filenames for technical documents where the established repository structure requires them.
- Keep code examples syntactically correct and free of embedded credentials.
- Distinguish read-only inspection from commands that modify security controls.
- Explain prerequisites, required permissions, limitations, failure modes, and verification steps for operational procedures.
- Use Mermaid diagrams only when they clarify trust relationships, request flows, or architecture boundaries.
- Verify AWS-specific behavior against authoritative AWS documentation when external verification is required.
- End each technical document with a `## Key Takeaways` section containing four or five concise bullets.
- Update this README's navigation whenever the directory structure changes.

## Key Takeaways

- AWS security depends on coordinated identity, network, application, cryptographic, and monitoring controls.
- Prefer short-lived workload credentials, least-privilege policies, and explicit trust boundaries over broad or long-lived access.
- Protect secrets and encryption keys through controlled access, lifecycle management, and verified operational procedures.
- Use centralized audit evidence and security findings to investigate incidents and validate security posture.
- Diagnose failures with scoped inspection and evidence-driven reasoning instead of indiscriminately granting permissions.