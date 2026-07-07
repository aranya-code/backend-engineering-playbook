# Common Interview Questions

This section covers frequently asked AWS Security interview questions at the senior DevOps / solutions architect level. Each question includes a detailed answer suitable for technical interviews.

---

# Identity and Access Management

## Q1: What is the AWS Shared Responsibility Model?

A framework that divides security responsibilities between AWS and the customer. AWS is responsible for security **of** the cloud (infrastructure, hardware, networking, managed services). The customer is responsible for security **in** the cloud (data, IAM, encryption, network configuration, application code).

The division shifts based on service type: EC2 (customer manages OS), RDS (AWS manages OS/engine), Lambda (AWS manages everything except code and IAM).

---

## Q2: What is the principle of least privilege and how do you implement it in AWS?

Least privilege means granting only the minimum permissions required to perform a task. Implementation:

- Start with no permissions and add specific actions as needed
- Use IAM policy conditions (source IP, MFA, time-based)
- Apply permission boundaries to set maximum permission limits
- Use IAM Access Analyzer to identify unused permissions
- Regularly audit and tighten policies
- Use service-linked roles with pre-defined, scoped permissions

---

## Q3: What is the difference between IAM Roles and IAM Users?

| Aspect | IAM User | IAM Role |
|--------|----------|----------|
| Credentials | Long-term (password, access keys) | Temporary (STS tokens) |
| Identity | Specific person or application | Assumed by anyone/anything allowed |
| Use case | Human console access | EC2, Lambda, cross-account, federation |
| Best practice | Minimize usage | Preferred for all service-to-service auth |

---

# Encryption

## Q4: Explain envelope encryption and why AWS KMS uses it.

Envelope encryption uses a two-tier key system:
1. A **data key** encrypts the actual data locally
2. A **KMS master key** encrypts the data key

Why: KMS can only directly encrypt data up to 4 KB. For larger data, you call `GenerateDataKey` to get a plaintext data key, encrypt data locally with AES-256, then store the encrypted data key alongside the encrypted data. This avoids sending large data over the network to KMS and reduces API costs.

---

## Q5: What is the difference between SSE-S3, SSE-KMS, and SSE-C?

| Feature | SSE-S3 | SSE-KMS | SSE-C |
|---------|--------|---------|-------|
| Key management | AWS fully managed | Customer controls via KMS | Customer provides key per request |
| Audit trail | No | Yes (CloudTrail) | No (AWS doesn't store key) |
| Key rotation | Automatic (opaque) | Configurable (auto or manual) | Customer responsibility |
| Cost | Free | KMS API costs | Free (but HTTPS required) |
| Default | Yes (since Jan 2023) | Opt-in | Opt-in |

---

## Q6: What is the difference between KMS and CloudHSM?

KMS is a multi-tenant, fully managed key management service (FIPS 140-2 Level 2). CloudHSM is a single-tenant, dedicated hardware security module (FIPS 140-2 Level 3). Use KMS for most workloads; use CloudHSM for strict regulatory requirements or custom cryptographic operations.

---

# Network Security

## Q7: What is the difference between Security Groups and NACLs?

Security Groups are stateful, instance-level, allow-only firewalls evaluated as a whole. NACLs are stateless, subnet-level firewalls with allow and deny rules evaluated in order. Security Groups are the primary control; NACLs provide additional subnet-level guardrails.

Key implication: NACLs require explicit rules for return traffic (ephemeral ports 1024-65535) because they are stateless.

---

## Q8: How would you design a secure VPC for a three-tier web application?

```text
VPC (10.0.0.0/16)
├── Public Subnet: ALB only
│   SG: Allow 443 from 0.0.0.0/0
├── Private Subnet (App): EC2/ECS
│   SG: Allow 8080 from ALB SG only
├── Private Subnet (Data): RDS
│   SG: Allow 5432 from App SG only
├── VPC Endpoints: S3, Secrets Manager
├── NAT Gateway: For app tier outbound
├── Flow Logs: Enabled → S3 + CloudWatch
└── No SSH from internet (use SSM Session Manager)
```

---

## Q9: Why should you use VPC Endpoints instead of NAT Gateways for AWS service access?

VPC Endpoints provide private connectivity to AWS services without traversing the internet. Benefits: reduced attack surface, lower data transfer costs (Gateway Endpoints are free), compliance with private connectivity requirements, better network performance.

---

# Threat Detection

## Q10: How does AWS GuardDuty work?

GuardDuty is a managed threat detection service that analyzes CloudTrail events, VPC Flow Logs, DNS query logs, EKS audit logs, and other sources using machine learning and threat intelligence. It produces findings with severity levels (Low, Medium, High, Critical) that can trigger automated remediation via EventBridge + Lambda.

GuardDuty does not require you to enable these data sources separately — it accesses them independently.

---

## Q11: How would you build an automated incident response for a compromised EC2 instance?

```text
1. GuardDuty detects anomalous behavior (e.g., crypto mining)
2. Finding sent to EventBridge
3. EventBridge rule triggers Lambda
4. Lambda:
   a. Creates forensic EBS snapshot
   b. Replaces instance security group with isolation SG (no inbound/outbound)
   c. Tags instance as "quarantined"
   d. Sends SNS notification to security team
   e. Creates JIRA incident ticket
5. Security team investigates using snapshot in isolated forensic VPC
```

---

# Compliance

## Q12: How do you implement continuous compliance monitoring in AWS?

Deploy this stack in every account:
- **Config** with managed rules and conformance packs (CIS, PCI DSS, HIPAA)
- **Security Hub** for aggregated compliance scoring
- **CloudTrail** for complete audit trail
- **GuardDuty** for threat detection
- **Config auto-remediation** via SSM Automation for common violations
- **Audit Manager** for automated evidence collection

---

## Q13: What is the difference between CloudTrail and AWS Config?

CloudTrail records **who** performed **what** API action and **when** (audit trail). Config records **what** the current resource configuration **is** and whether it's **compliant** with rules. Together: CloudTrail tells you who changed a security group; Config tells you the security group is now non-compliant.

---

# Secrets and WAF

## Q14: When would you use Secrets Manager vs Parameter Store?

Use **Secrets Manager** when you need automatic rotation (especially for RDS/Aurora credentials), cross-account sharing, or cross-region replication. Cost: $0.40/secret/month.

Use **Parameter Store** (Standard tier) for hierarchical configuration management, simple secrets without rotation, or when cost matters. Cost: Free.

Common pattern: Use both — Parameter Store for configuration, Secrets Manager for rotated database credentials.

---

## Q15: How would you protect a web application from SQL injection and DDoS?

Layer 1: **CloudFront** — absorbs traffic at the edge, global distribution
Layer 2: **AWS Shield** — Standard (free, automatic L3/L4 DDoS) or Advanced ($3K/month, L7 + DRT)
Layer 3: **AWS WAF** — SQL injection detection rules (AWS Managed Core Rule Set), rate-based rules for brute force, IP reputation list
Layer 4: **ALB Security Groups** — restrict to CloudFront IP ranges
Layer 5: **Application input validation** — parameterized queries, output encoding

---

## Q16: What is the SigV4 signing process?

SigV4 authenticates AWS API requests using HMAC-SHA256. Four steps:
1. Create a **canonical request** (standardized HTTP request format)
2. Create a **string to sign** (includes date, region, service scope)
3. Derive a **signing key** (HMAC chain: secret key → date → region → service)
4. Calculate the **signature** (HMAC-SHA256 of string to sign with signing key)

The signature is sent in the Authorization header or as query string parameters (presigned URLs).

---

## Q17: How do you handle a leaked AWS access key?

Immediate actions:
1. **Deactivate** the access key in IAM (do not delete yet — for investigation)
2. **Revoke all active sessions** for the IAM user
3. **Audit CloudTrail** for any actions taken with the key
4. **Check for unauthorized resources** (EC2 instances, Lambda, IAM users)
5. **Rotate credentials** — create new key, update applications
6. **Delete** the compromised key after confirming the new key works
7. **Investigate** how the key was leaked (Git, logs, misconfiguration)
8. **Implement prevention** — switch to IAM Roles, use Secrets Manager

---
