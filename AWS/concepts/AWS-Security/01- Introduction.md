# AWS Security — Introduction

AWS Security is the practice of protecting cloud workloads, data, applications, and infrastructure running on Amazon Web Services from unauthorized access, vulnerabilities, and threats. Security is not a single service — it is a shared responsibility between AWS and the customer, implemented through a combination of identity management, encryption, network controls, monitoring, and compliance.

In the cloud, security is the **number one priority**. AWS provides over 200 security, compliance, and governance services and features, but the customer is ultimately responsible for how those services are configured and used.

---

# Why Cloud Security is Critical

Cloud environments introduce unique challenges compared to traditional data centers:

- Resources are accessible over the internet by default
- Infrastructure can be provisioned by anyone with API credentials
- Misconfigurations are the leading cause of cloud breaches
- Data is distributed across regions and services
- Shared infrastructure requires strong isolation guarantees

```text
Traditional Data Center          AWS Cloud
─────────────────────           ──────────────
Physical perimeter              API-based access
Manual provisioning             Automated provisioning
Limited blast radius            Global blast radius
Hardware security               Software-defined security
Slow to change                  Rapid change
```

---

# Security Pillars

AWS security can be organized into five core pillars:

## 1. Identity and Access Management

Control **who** can access **what** resources and **under what conditions**.

- IAM Users, Groups, Roles, Policies
- Federation (SAML, OIDC)
- AWS Organizations and SCPs
- Temporary credentials via STS

---

## 2. Detection and Monitoring

Detect threats, anomalies, and unauthorized activity in real time.

- AWS CloudTrail (API audit logging)
- Amazon GuardDuty (threat detection)
- AWS Security Hub (centralized findings)
- Amazon CloudWatch (metrics and alarms)
- VPC Flow Logs (network traffic analysis)

---

## 3. Infrastructure Protection

Protect networks, compute resources, and workloads.

- VPC (subnets, security groups, NACLs)
- AWS WAF (web application firewall)
- AWS Shield (DDoS protection)
- AWS Firewall Manager
- Systems Manager (patch management)

---

## 4. Data Protection

Protect data at rest and in transit using encryption and access controls.

- AWS KMS (key management)
- Server-side encryption (SSE-S3, SSE-KMS, SSE-C)
- Client-side encryption
- TLS/SSL for data in transit
- AWS Certificate Manager (ACM)
- Macie (sensitive data discovery)

---

## 5. Incident Response

Respond to security events quickly and effectively.

- Automated remediation with EventBridge + Lambda
- Forensic analysis with CloudTrail and VPC Flow Logs
- Isolation procedures
- Runbook automation with Systems Manager

---

# Defense in Depth

AWS security follows a **defense in depth** strategy — multiple layers of security controls so that if one layer fails, the next layer provides protection.

```text
┌─────────────────────────────────────────────┐
│              Edge Security                  │
│    (CloudFront, WAF, Shield, Route 53)      │
├─────────────────────────────────────────────┤
│            Network Security                 │
│    (VPC, Subnets, NACLs, Security Groups)   │
├─────────────────────────────────────────────┤
│           Compute Security                  │
│    (EC2 hardening, SSM, Inspector)          │
├─────────────────────────────────────────────┤
│          Application Security               │
│    (WAF rules, input validation, secrets)   │
├─────────────────────────────────────────────┤
│            Data Security                    │
│    (Encryption, KMS, Macie, access control) │
├─────────────────────────────────────────────┤
│         Identity & Access                   │
│    (IAM, STS, Organizations, SCPs)          │
├─────────────────────────────────────────────┤
│       Monitoring & Detection                │
│    (CloudTrail, GuardDuty, Security Hub)    │
└─────────────────────────────────────────────┘
```

No single layer provides complete protection. The combination of all layers creates a robust security posture.

---

# AWS Security Services Landscape

| Category | Services |
|----------|----------|
| **Identity** | IAM, STS, Organizations, SSO (Identity Center), Cognito |
| **Detection** | GuardDuty, Security Hub, CloudTrail, Inspector, Macie |
| **Network** | VPC, WAF, Shield, Firewall Manager, Network Firewall |
| **Encryption** | KMS, CloudHSM, ACM, Secrets Manager |
| **Compliance** | Config, Audit Manager, Artifact |
| **Incident Response** | EventBridge, Lambda, Systems Manager, Detective |

---

# Common Cloud Security Threats

| Threat | Description | AWS Mitigation |
|--------|-------------|----------------|
| Misconfiguration | Open S3 buckets, permissive security groups | Config Rules, Access Analyzer |
| Credential theft | Leaked access keys, compromised IAM users | STS temporary credentials, MFA, key rotation |
| Data exfiltration | Unauthorized data transfer | Macie, VPC endpoints, S3 Block Public Access |
| DDoS attacks | Volumetric, protocol, application layer attacks | Shield, WAF, CloudFront |
| Privilege escalation | Overly permissive IAM policies | IAM Access Analyzer, least privilege |
| Injection attacks | SQL injection, XSS, command injection | WAF managed rules, input validation |
| Insider threats | Malicious or negligent internal actors | CloudTrail, GuardDuty, least privilege |

---

# Key Takeaways

- Security in AWS is a **shared responsibility** between AWS and the customer.
- AWS secures the cloud infrastructure; the customer secures what runs inside it.
- Security should be implemented in **layers** (defense in depth).
- **Identity and access management** is the foundation of cloud security.
- **Encryption** should be applied to data at rest and in transit by default.
- **Monitoring and detection** services provide visibility into threats.
- Misconfigurations — not sophisticated attacks — are the most common cause of cloud security breaches.
- Every AWS service has security implications that must be understood and configured correctly.

---
