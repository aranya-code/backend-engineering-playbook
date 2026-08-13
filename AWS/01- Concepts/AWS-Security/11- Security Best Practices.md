# Security Best Practices

This guide provides a comprehensive production security hardening checklist for AWS environments. These best practices are drawn from the AWS Well-Architected Framework Security Pillar, CIS AWS Foundations Benchmark, and real-world operational experience.

Following these practices systematically reduces your attack surface, improves compliance posture, and builds a defense-in-depth security architecture.

---

# Root Account Protection

The root account has unrestricted access to everything in the AWS account. Compromising it means total account takeover.

- **Enable MFA** on the root account (hardware MFA preferred)
- **Never create access keys** for the root account
- **Never use the root account** for daily operations
- **Use a strong, unique password** stored in a secure vault
- **Set up alerts** for root account usage via CloudTrail + EventBridge
- **Lock the root email** with MFA on the email provider

```text
Root Account Usage: EMERGENCY ONLY

✗ Daily operations
✗ Creating resources
✗ Deploying applications

✓ Changing account settings
✓ Enabling MFA on root
✓ Restoring IAM permissions
✓ Closing the account
```

---

# IAM Best Practices

## Least Privilege

Grant only the minimum permissions required to perform a task.

- Start with zero permissions and add as needed
- Use **IAM Access Analyzer** to identify unused permissions
- Review and tighten permissions regularly
- Use **permission boundaries** to set maximum permission limits

## Credential Management

- Use **IAM Roles** instead of long-term access keys wherever possible
- **Rotate access keys** every 90 days for users that must have them
- **Never embed credentials** in application code
- Use **Secrets Manager** or **Parameter Store** for secrets
- Enable **MFA** for all IAM users with console access

## Organizations and SCPs

- Use **AWS Organizations** for multi-account architecture
- Apply **Service Control Policies (SCPs)** to restrict account capabilities
- Create dedicated accounts for: workloads, security/audit, logging, sandbox

```text
Organization Structure:

Management Account (billing, SCPs)
├── Security Account (GuardDuty admin, Security Hub admin)
├── Log Archive Account (centralized CloudTrail, Config)
├── Production OU
│   ├── Prod Account A
│   └── Prod Account B
├── Development OU
│   ├── Dev Account A
│   └── Dev Account B
└── Sandbox OU
    └── Sandbox Account
```

---

# Network Security Checklist

| Practice | Implementation |
|----------|---------------|
| Use private subnets for applications | ALB in public, app/data in private |
| Restrict security group rules | Only required ports, reference SGs not CIDRs |
| Never open SSH (22) to 0.0.0.0/0 | Use SSM Session Manager instead |
| Enable VPC Flow Logs | Send to CloudWatch and S3 |
| Use VPC Endpoints | Private connectivity to S3, DynamoDB, and other services |
| Segment networks | Separate subnets per tier, NACLs as guardrails |
| Use PrivateLink | For internal service-to-service communication |
| Enable DNS logging | Route 53 Resolver query logging |

---

# Encryption Checklist

| Practice | Implementation |
|----------|---------------|
| Encrypt all data at rest | Enable encryption on S3, EBS, RDS, DynamoDB |
| Encrypt all data in transit | Use TLS 1.2+ for all connections |
| Use KMS customer managed keys | For production workloads requiring audit trails |
| Enforce encryption via policies | S3 bucket policies, SCPs, Config rules |
| Enforce HTTPS | S3 `aws:SecureTransport`, ALB redirect |
| Manage certificates with ACM | Free SSL/TLS certificates for AWS services |
| Rotate keys | Enable automatic key rotation in KMS |

---

# Monitoring and Detection Stack

Deploy this monitoring stack in every account:

```text
┌────────────────────────────────────────────┐
│           Security Monitoring Stack        │
│                                            │
│  CloudTrail ──► S3 (long-term storage)     │
│             ──► CloudWatch (real-time)     │
│                                            │
│  GuardDuty ──► EventBridge ──► Lambda      │
│                              (remediation) │
│                                            │
│  Security Hub ──► Dashboard               │
│               ──► Compliance scores       │
│                                            │
│  Config ──► Rules ──► Auto-remediation    │
│                                            │
│  VPC Flow Logs ──► CloudWatch / S3        │
│                                            │
│  IAM Access Analyzer ──► Findings         │
└────────────────────────────────────────────┘
```

---

# Incident Response

## Preparation

- Create and maintain an **incident response plan**
- Define **severity levels** and **escalation procedures**
- Pre-provision forensic tools and **isolated VPC** for investigation
- Create **automation runbooks** in SSM for common scenarios
- Conduct regular **tabletop exercises**

## Common Automated Response Actions

| Trigger | Automated Action |
|---------|-----------------|
| Compromised EC2 instance | Isolate with restrictive security group, snapshot EBS |
| Leaked access key | Deactivate key, revoke active sessions |
| Publicly exposed S3 bucket | Re-enable Block Public Access |
| Unusual API activity from IAM user | Attach deny-all policy, notify security team |
| SSH brute force detection | Block source IP in WAF / NACL |

---

# AWS Trusted Advisor Security Checks

Trusted Advisor provides automated security recommendations:

| Check | What It Detects |
|-------|----------------|
| S3 Bucket Permissions | Publicly accessible buckets |
| Security Groups | Unrestricted access (0.0.0.0/0) on sensitive ports |
| IAM Use | Root account access key usage |
| MFA on Root | Root account without MFA |
| CloudTrail Logging | CloudTrail not enabled |
| EBS Public Snapshots | Publicly shared EBS snapshots |
| RDS Public Snapshots | Publicly shared RDS snapshots |

---

# Production Security Hardening Checklist

```text
Account Level:
☐ Root MFA enabled (hardware key)
☐ No root access keys
☐ AWS Organizations with SCPs
☐ Dedicated security and logging accounts
☐ CloudTrail enabled (all regions, all accounts)
☐ GuardDuty enabled (all regions, all accounts)
☐ Security Hub enabled with compliance standards
☐ Config enabled with conformance packs

Network Level:
☐ VPC with public/private subnet separation
☐ Security groups with least privilege
☐ NACLs for subnet-level guardrails
☐ VPC Flow Logs enabled
☐ VPC Endpoints for AWS services
☐ No SSH/RDP from 0.0.0.0/0

Data Level:
☐ Encryption at rest enabled on all services
☐ Encryption in transit enforced (TLS 1.2+)
☐ KMS keys with appropriate key policies
☐ S3 Block Public Access enabled
☐ S3 bucket policies enforce HTTPS
☐ Secrets in Secrets Manager / Parameter Store

Identity Level:
☐ MFA for all console users
☐ IAM roles instead of access keys
☐ Permission boundaries on delegated roles
☐ Regular access reviews with Access Analyzer
☐ Credential rotation (90-day policy)
```

---

# Key Takeaways

- Security is a continuous process, not a one-time configuration.
- The root account is the most critical asset — protect it with MFA and never use it daily.
- Least privilege is the most impactful IAM practice — start with zero and add.
- Deploy GuardDuty, Security Hub, Config, and CloudTrail in every account and region.
- Automate remediation — don't rely on humans to fix every finding.
- Encrypt everything — at rest and in transit, by default.
- Network segmentation and VPC Endpoints reduce your attack surface.
- Regular security reviews and incident response exercises are essential.

---
