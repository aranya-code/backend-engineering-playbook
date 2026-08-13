# README

## Overview

This folder covers the security architecture and operational security practices required to run Amazon Elastic Beanstalk applications in production.

The material progresses from the overall security model through identity, network controls, transport encryption, data protection, secrets management, auditing, edge protection, compliance monitoring, and production security practices.

The focus is on securing the complete application environment rather than treating Elastic Beanstalk as an isolated service.

## Security Architecture

A production Elastic Beanstalk security model should use multiple independent layers:

```text
                         Internet
                            │
                            ▼
                    Route 53 / CloudFront
                            │
                            ▼
                         AWS WAF
                            │
                            ▼
                   Application Load Balancer
                            │
                     HTTPS / TLS
                            │
                            ▼
                 Elastic Beanstalk Environment
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
       Application Tier              Worker Tier
              │                           │
              └─────────────┬─────────────┘
                            │
                 ┌──────────┴──────────┐
                 │                     │
                 ▼                     ▼
             PostgreSQL             Redis
                 │                     │
                 └──────────┬──────────┘
                            │
                            ▼
                 Monitoring & Auditing
```

Security responsibilities are distributed across several layers:

| Layer | Primary controls |
|---|---|
| Identity | IAM, least privilege, roles |
| Network | VPC, subnets, security groups |
| Transport | HTTPS, TLS, secure cookies |
| Edge | WAF, rate limiting, DDoS protection |
| Application | Authentication, authorization, validation |
| Data | Encryption, database access controls, backups |
| Secrets | Secrets Manager, Parameter Store, rotation |
| Runtime | EC2 roles, platform patching, container security |
| Monitoring | CloudTrail, CloudWatch, WAF logs, audit logs |
| Operations | CI/CD controls, access reviews, incident response |

## Documentation

| File | Coverage |
|---|---|
| [01- Security Overview](./01-%20Security%20Overview.md) | Security model, shared responsibility, defense in depth, and the major security boundaries of an Elastic Beanstalk environment |
| [02- IAM and Access Control](./02-%20IAM%20and%20Access%20Control.md) | IAM users, roles, instance profiles, service roles, least privilege, deployment identities, and access control |
| [03- Network Security](./03-%20Network%20Security.md) | VPC placement, subnets, security groups, ingress, egress, administrative access, and network isolation |
| [04- HTTPS and TLS Security](./04-%20HTTPS%20and%20TLS%20Security.md) | HTTPS, TLS termination, certificates, secure communication, redirects, cookies, and transport security |
| [05- Encryption and Data Protection](./05-%20Encryption%20and%20Data%20Protection.md) | Encryption at rest and in transit, database protection, S3 security, backups, and sensitive-data handling |
| [06- Secrets Management](./06-%20Secrets%20Management.md) | Secrets Manager, Parameter Store, runtime secret injection, credential rotation, and secret-handling practices |
| [07- Logging and Auditing](./07-%20Logging%20and%20Auditing.md) | CloudTrail, CloudWatch, application logs, access logs, audit trails, retention, and security event visibility |
| [08- WAF and DDoS Protection](./08-%20WAF%20and%20DDoS%20Protection.md) | AWS WAF, managed rules, rate limiting, request filtering, and DDoS-aware application architecture |
| [09- Security Monitoring and Compliance](./09-%20Security%20Monitoring%20and%20Compliance.md) | Continuous security monitoring, findings, configuration monitoring, compliance controls, and operational visibility |
| [10- Security Best Practices](./10-%20Security%20Best%20Practices.md) | Production security baseline, hardening checklist, common mistakes, operational practices, and interview considerations |

## Recommended Reading Order

Read the documents in numerical order.

```text
01- Security Overview
        │
        ▼
02- IAM and Access Control
        │
        ▼
03- Network Security
        │
        ▼
04- HTTPS and TLS Security
        │
        ▼
05- Encryption and Data Protection
        │
        ▼
06- Secrets Management
        │
        ▼
07- Logging and Auditing
        │
        ▼
08- WAF and DDoS Protection
        │
        ▼
09- Security Monitoring and Compliance
        │
        ▼
10- Security Best Practices
```

This order moves from security fundamentals to infrastructure controls, application transport security, data protection, operational visibility, edge protection, and finally production hardening.

## Security Control Matrix

| Security concern | Primary control | Supporting controls |
|---|---|---|
| Unauthorized AWS access | IAM | MFA, least privilege, access reviews |
| Compromised application | IAM instance role | Network restrictions, monitoring |
| Public database exposure | Security groups | Private subnets, database authentication |
| Credential interception | TLS | Secure cookies, HSTS |
| Secret leakage | Secrets Manager / Parameter Store | IAM, rotation, log filtering |
| Malicious HTTP traffic | AWS WAF | Application validation, rate limiting |
| DDoS | AWS edge services | WAF, CloudFront, resilient architecture |
| Data theft | Encryption | IAM, network isolation, auditing |
| Unauthorized infrastructure changes | CloudTrail | IAM, CI/CD controls, configuration monitoring |
| Security incident | Centralized monitoring | Alerting, incident response, recovery |
| Supply-chain vulnerability | Dependency scanning | Image scanning, patch management |
| Configuration drift | Infrastructure as Code | Code review, controlled deployments |

## Production Security Baseline

A production Elastic Beanstalk environment should generally establish the following baseline:

### Identity

- Use IAM roles instead of long-lived application credentials.
- Apply least privilege to application and deployment roles.
- Separate developer, CI/CD, runtime, and administrative access.
- Protect privileged identities with strong authentication.
- Review permissions periodically.

### Network

- Use appropriate VPC and subnet isolation.
- Keep databases and internal services private.
- Restrict security-group rules to required traffic.
- Minimize publicly exposed ports.
- Restrict administrative access.
- Monitor network activity where required.

### Application

- Enforce authentication and authorization server-side.
- Validate untrusted input.
- Protect sensitive endpoints against abuse.
- Keep dependencies patched.
- Prevent secrets from entering source code and logs.
- Apply secure framework configuration.

### Data

- Encrypt sensitive data at rest.
- Use TLS for sensitive data in transit.
- Restrict database access.
- Protect backups.
- Apply appropriate data-retention policies.
- Classify sensitive data according to organizational requirements.

### Secrets

- Store secrets in managed secret-storage services.
- Avoid committing credentials to Git.
- Do not embed secrets in container images.
- Restrict secret access through IAM.
- Establish rotation procedures.
- Prevent secret values from appearing in logs.

### Edge Protection

- Use HTTPS for external traffic.
- Consider AWS WAF for HTTP-layer protection.
- Apply rate limiting where appropriate.
- Design the architecture with DDoS resilience in mind.

### Monitoring

- Enable appropriate CloudTrail auditing.
- Centralize application and infrastructure logs.
- Monitor security-relevant events.
- Monitor WAF activity.
- Monitor IAM and infrastructure changes.
- Establish alerts for important security signals.

### Operations

- Use controlled CI/CD deployments.
- Version infrastructure configuration.
- Scan dependencies and container images.
- Keep the Elastic Beanstalk platform supported.
- Maintain backups.
- Test recovery procedures.
- Maintain an incident-response process.

## Security Model

The most important principle across this folder is **defense in depth**.

No single control should be expected to protect the entire application.

```text
                ┌─────────────────────┐
                │       Identity      │
                │   IAM / Roles       │
                └──────────┬──────────┘
                           │
                ┌──────────▼──────────┐
                │       Network       │
                │ VPC / SG / Subnets  │
                └──────────┬──────────┘
                           │
                ┌──────────▼──────────┐
                │      Transport      │
                │     HTTPS / TLS     │
                └──────────┬──────────┘
                           │
                ┌──────────▼──────────┐
                │        Edge         │
                │    WAF / DDoS       │
                └──────────┬──────────┘
                           │
                ┌──────────▼──────────┐
                │     Application     │
                │ Auth / Validation   │
                └──────────┬──────────┘
                           │
                ┌──────────▼──────────┐
                │        Data         │
                │ DB / S3 / Redis     │
                └──────────┬──────────┘
                           │
                ┌──────────▼──────────┐
                │ Monitoring / Audit  │
                │ Logs / Findings     │
                └─────────────────────┘
```

A failure of one layer should not automatically result in unrestricted access to the rest of the system.

## Backend Engineering Context

Elastic Beanstalk security should be considered together with the backend architecture.

For a Django or FastAPI application, a typical production request path is:

```text
Client
  │
  │ HTTPS
  ▼
CloudFront / WAF
  │
  ▼
Application Load Balancer
  │
  ▼
Elastic Beanstalk
  │
  ▼
Django / FastAPI
  │
  ├── PostgreSQL
  ├── Redis
  ├── S3
  └── AWS APIs through IAM role
```

Each dependency introduces its own security boundary.

For example:

- IAM controls whether the application can call AWS APIs.
- Security groups control network connectivity.
- Database permissions control database operations.
- Application authorization controls what an authenticated user can do.
- WAF filters HTTP traffic.
- TLS protects data in transit.
- Monitoring provides visibility into security events.

Understanding these boundaries is essential when designing or reviewing production backend systems.

## Common Security Mistakes

The following mistakes should be specifically avoided:

| Mistake | Risk |
|---|---|
| `0.0.0.0/0` access to PostgreSQL | Public database exposure |
| Public Redis | Data exposure and attack surface |
| Administrator permissions for applications | Excessive blast radius |
| AWS access keys stored on EC2 | Credential theft |
| Secrets committed to Git | Persistent credential exposure |
| Secrets embedded in Docker images | Credential leakage through image layers |
| HTTP-only production APIs | Credential and data interception |
| No application authorization | Broken access control |
| No audit logging | Poor incident investigation |
| Relying only on WAF | Application vulnerabilities remain |
| Manual production changes | Configuration drift |
| Unpatched dependencies | Known vulnerabilities remain exploitable |
| Untested backups | Recovery failure during incidents |

## Quick Navigation

### Architecture

- [Security Overview](./01-%20Security%20Overview.md)
- [IAM and Access Control](./02-%20IAM%20and%20Access%20Control.md)
- [Network Security](./03-%20Network%20Security.md)
- [HTTPS and TLS Security](./04-%20HTTPS%20and%20TLS%20Security.md)

### Data and Secrets

- [Encryption and Data Protection](./05-%20Encryption%20and%20Data%20Protection.md)
- [Secrets Management](./06-%20Secrets%20Management.md)

### Monitoring and Protection

- [Logging and Auditing](./07-%20Logging%20and%20Auditing.md)
- [WAF and DDoS Protection](./08-%20WAF%20and%20DDoS%20Protection.md)
- [Security Monitoring and Compliance](./09-%20Security%20Monitoring%20and%20Compliance.md)

### Production Hardening

- [Security Best Practices](./10-%20Security%20Best%20Practices.md)

## Key Takeaways

- Treat Elastic Beanstalk security as a layered architecture rather than a single service configuration.
- Start with least-privilege IAM and strong identity boundaries.
- Keep internal infrastructure private and minimize exposed network paths.
- Protect external traffic with HTTPS and appropriate TLS configuration.
- Protect sensitive data at rest and in transit.
- Use managed secret storage instead of source code, Git, or container images.
- Use WAF and rate limiting as additional edge defenses where appropriate.
- Centralize logging and auditing so security events can be investigated.
- Secure the application itself; AWS infrastructure controls do not replace application authorization and validation.
- Secure CI/CD because deployment credentials can provide a path to the entire environment.
- Treat security monitoring, compliance, incident response, and recovery as ongoing operational responsibilities.
- Use the individual documents in this folder as a complete security reference for designing, deploying, and operating production Elastic Beanstalk workloads.