# README

## Overview

This directory contains security-focused documentation for AWS Lambda within the `backend-engineering-playbook`. It covers the security boundaries, identity and access management, invocation authorization, secrets protection, network security, dependency integrity, auditing, compliance, and production security practices required to operate Lambda workloads safely.

The documentation is intended for backend engineers progressing from foundational AWS knowledge to senior-level serverless engineering. It emphasizes practical implementation, least-privilege access, secure deployment workflows, threat mitigation, and operational verification.

## Scope and Organization

The security documentation is organized around distinct security responsibilities:

| Area | Purpose |
|---|---|
| Security fundamentals | Understand Lambda's security model and shared responsibility boundaries |
| IAM and authorization | Control execution permissions, invocation permissions, and access to AWS resources |
| Secrets and configuration | Protect credentials, environment variables, and sensitive configuration |
| Network security | Restrict network access and secure VPC-connected workloads |
| Dependency and artifact security | Reduce supply-chain risks across packages, layers, and container images |
| Auditing and compliance | Collect security evidence, evaluate configuration, and investigate changes |
| Security best practices | Apply consistent controls across development, deployment, and production operations |

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- Lambda Security Overview](./01-%20Lambda%20Security%20Overview.md) | Introduces Lambda security boundaries, the shared responsibility model, threat categories, and core defensive controls. |
| 02 | [02- IAM Execution Roles and Permissions](./02-%20IAM%20Execution%20Roles%20and%20Permissions.md) | Explains execution roles, trust policies, identity-based policies, least privilege, and runtime access to AWS services. |
| 03 | [03- Resource-Based Policies and Invocation Permissions](./03-%20Resource-Based%20Policies%20and%20Invocation%20Permissions.md) | Covers Lambda resource policies, invocation authorization, service principals, and cross-account access. |
| 04 | [04- Environment Variables and Secrets Protection](./04-%20Environment%20Variables%20and%20Secrets%20Protection.md) | Covers environment-variable protection, AWS Secrets Manager, Systems Manager Parameter Store, and credential lifecycle management. |
| 05 | [05- VPC and Network Security](./05-%20VPC%20and%20Network%20Security.md) | Explains VPC attachment, subnet selection, security groups, routing, private connectivity, DNS, and outbound network controls. |
| 06 | [06- Dependency and Deployment Package Security](./06-%20Dependency%20and%20Deployment%20Package%20Security.md) | Covers dependency vulnerabilities, trusted build artifacts, ZIP packages, Lambda layers, and container-image security. |
| 07 | [07- Least Privilege and Permission Boundaries](./07-%20Least%20Privilege%20and%20Permission%20Boundaries.md) | Examines least-privilege design, permission boundaries, policy evaluation, and controls that constrain excessive permissions. |
| 08 | [08- Security Auditing and Compliance](./08-%20Security%20Auditing%20and%20Compliance.md) | Covers CloudTrail, CloudWatch Logs, AWS Config, security findings, audit evidence, retention, and incident investigation. |
| 09 | [09- Lambda Security Best Practices](./09-%20Lambda%20Security%20Best%20Practices.md) | Consolidates practical security controls for identity, input validation, secrets, dependencies, networking, event processing, monitoring, and CI/CD. |

## Recommended Reading Order

Follow the sequence below to build a complete understanding of Lambda security.

1. **Understand the security model:** Start with the security overview and identify the boundaries between AWS-managed infrastructure and application-owner responsibilities.
2. **Establish identity controls:** Study execution roles, permissions, resource-based policies, invocation authorization, and permission boundaries.
3. **Protect data and network access:** Review secret management, environment variables, VPC configuration, and network restrictions.
4. **Secure the software supply chain:** Understand dependency management, deployment package integrity, and container-image security.
5. **Implement auditability:** Learn how to collect, protect, retain, and investigate security evidence.
6. **Apply production controls:** Use the best-practices document as a consolidated implementation and review checklist.

## Core Security Principles

### Least Privilege

Every Lambda function should receive only the permissions needed for its responsibilities. Avoid broad wildcard permissions and unnecessary access to unrelated resources.

### Defense in Depth

Combine IAM, resource-based policies, network controls, application validation, secret protection, and monitoring. No single control should be treated as sufficient for every threat.

### Secure Deployment

Restrict who can build, publish, and deploy Lambda code. Separate deployment permissions from runtime permissions, protect CI/CD credentials, and verify release artifacts.

### Data Protection

Use managed secret stores, appropriate encryption, restrictive access policies, and deliberate retention periods. Prevent credentials and sensitive payloads from appearing in application logs.

### Continuous Auditing

Monitor security-relevant changes, evaluate supported configuration requirements, investigate findings, and test that the required audit evidence is actually being collected.

### Operational Resilience

Design event processing for duplicate delivery, retries, malformed input, concurrency spikes, and downstream failures. Security controls should not depend on every invocation succeeding exactly once.

## Production Security Review

Use this checklist when reviewing a Lambda function before production deployment or during periodic security assessments.

### Identity and Authorization

- [ ] The execution role follows least-privilege principles.
- [ ] Invocation permissions are explicit and appropriately scoped.
- [ ] Cross-account access and service principals are reviewed.
- [ ] Deployment identities are separate from runtime identities.
- [ ] IAM trust policies, `iam:PassRole`, and permission boundaries are reviewed where applicable.

### Code and Data

- [ ] Dependencies are reviewed and scanned for vulnerabilities.
- [ ] Deployment artifacts come from a controlled build process.
- [ ] Input validation and application-level authorization are implemented.
- [ ] Secrets are stored and accessed through approved mechanisms.
- [ ] Logs avoid credentials and unnecessary sensitive data.
- [ ] Duplicate events and retries are handled safely.

### Network and Runtime

- [ ] VPC routing, security groups, DNS, and service connectivity are reviewed.
- [ ] Database access is restricted and connection limits are considered.
- [ ] Timeouts, concurrency, and retry policies are configured intentionally.
- [ ] Recursive invocation risks and failure-handling paths are addressed.

### Monitoring and Compliance

- [ ] CloudTrail collects the required management events.
- [ ] Required data events are explicitly configured and verified.
- [ ] CloudWatch logs, metrics, and alarms support operational diagnosis.
- [ ] Audit records have appropriate access and retention controls.
- [ ] Security findings have clear ownership and response procedures.
- [ ] Incident response, credential rotation, and rollback procedures have been tested.

## Related Engineering Areas

Lambda security should be reviewed alongside the broader engineering practices that influence runtime behavior and deployment safety.

| Related area | Security relevance |
|---|---|
| Lambda IAM and authorization | Determines which identities can invoke functions and which resources functions can access |
| Lambda networking | Defines reachable resources and network communication paths |
| Lambda deployment and CI/CD | Controls artifact provenance, deployment authority, and release integrity |
| Lambda monitoring and observability | Provides evidence for incident detection, investigation, and operational response |
| Lambda event processing | Addresses duplicate delivery, retry behavior, input validation, and failure isolation |
| AWS account governance | Establishes organization-level guardrails, account boundaries, and centralized audit controls |

## Documentation Standards

Maintain these documents as a focused engineering reference:

- Keep each document centered on one security responsibility.
- Use practical examples and verification procedures rather than generic recommendations.
- Explain security trade-offs, operational consequences, and common misconfigurations.
- Cross-reference related documents instead of duplicating detailed explanations.
- Validate AWS capabilities, permissions, and service limitations against current official documentation.
- Update security guidance when architecture, runtime support, organizational requirements, or AWS service behavior changes.

## Key Takeaways

- Lambda security requires coordinated controls across IAM, invocation authorization, application code, networking, data protection, and deployment.
- Use the individual documents to understand each security boundary, then apply the consolidated best-practices checklist during production reviews.
- Audit configuration changes and runtime behavior through complementary services, and verify that required logging and evidence collection are enabled.
- Treat dependency integrity, CI/CD permissions, secret lifecycle management, and duplicate-event handling as core parts of production security.
- Keep security documentation aligned with the actual repository structure and validate its technical guidance against current AWS documentation.