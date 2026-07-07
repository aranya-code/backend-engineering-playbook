# AWS GuardDuty and Security Hub

AWS GuardDuty and AWS Security Hub are complementary security services that provide **threat detection** and **centralized security management**. GuardDuty continuously analyzes data sources to detect malicious activity and unauthorized behavior, while Security Hub aggregates security findings from GuardDuty and other services into a single dashboard with compliance checks.

Together, they form the detection and visibility layer of a comprehensive AWS security architecture.

---

# AWS GuardDuty

## What is GuardDuty?

AWS GuardDuty is a **fully managed intelligent threat detection service** that continuously monitors AWS accounts and workloads for malicious activity, unauthorized behavior, and anomalous patterns.

GuardDuty uses **machine learning**, **anomaly detection**, and **threat intelligence feeds** to identify threats — requiring no infrastructure to deploy or manage.

```text
Data Sources                   GuardDuty                    Response
                                  │
CloudTrail Events ──────────►     │
VPC Flow Logs ──────────────►  Analysis  ──► Findings ──► EventBridge
DNS Query Logs ─────────────►  Engine       (Severity)     │
S3 Data Events ─────────────►     │                        ▼
EKS Audit Logs ─────────────►     │                    Lambda
Lambda Network Activity ────►     │                 (Auto-Remediation)
```

## Data Sources Analyzed

| Data Source | What GuardDuty Learns |
|-------------|----------------------|
| **CloudTrail Management Events** | API calls, IAM activity, resource changes |
| **CloudTrail S3 Data Events** | S3 object-level operations |
| **VPC Flow Logs** | Network traffic patterns, port scanning, data exfiltration |
| **DNS Query Logs** | Communication with known malicious domains |
| **EKS Audit Logs** | Kubernetes API activity, suspicious pod behavior |
| **Lambda Network Activity** | Unusual Lambda networking patterns |
| **RDS Login Activity** | Anomalous database login attempts |

GuardDuty does **not** require you to enable these data sources separately — it analyzes them independently at no additional logging cost.

---

## Finding Types

GuardDuty categorizes findings by resource type and threat category:

### EC2 Findings

| Finding | Description |
|---------|-------------|
| `Backdoor:EC2/DenialOfService` | EC2 used in a DDoS attack |
| `CryptoCurrency:EC2/BitcoinTool` | EC2 communicating with crypto mining pools |
| `Trojan:EC2/BlackholeTraffic` | EC2 sending traffic to a black hole |
| `UnauthorizedAccess:EC2/SSHBruteForce` | SSH brute force detected |
| `Recon:EC2/PortProbeUnprotectedPort` | Port scanning from EC2 |

### IAM Findings

| Finding | Description |
|---------|-------------|
| `UnauthorizedAccess:IAMUser/MaliciousIPCaller` | API call from a known malicious IP |
| `Discovery:IAMUser/AnomalousBehavior` | Unusual API discovery patterns |
| `Persistence:IAMUser/AnomalousBehavior` | Unusual persistence activity |

### S3 Findings

| Finding | Description |
|---------|-------------|
| `Exfiltration:S3/MaliciousIPCaller` | S3 access from a malicious IP |
| `Policy:S3/BucketBlockPublicAccessDisabled` | Public access block removed |
| `UnauthorizedAccess:S3/TorIPCaller` | S3 accessed from a Tor exit node |

## Severity Levels

| Severity | Range | Meaning |
|----------|-------|---------|
| **Low** | 1.0 – 3.9 | Suspicious but potentially benign |
| **Medium** | 4.0 – 6.9 | Suspicious activity that deviates from normal |
| **High** | 7.0 – 8.9 | Resource is compromised and actively exploited |
| **Critical** | 9.0 – 10.0 | Immediate action required |

---

## Automated Remediation

GuardDuty integrates with EventBridge to trigger automated responses:

```text
GuardDuty Finding
       │
       ▼
  EventBridge Rule
  (Match finding type + severity)
       │
       ▼
  Lambda Function
  ├── Isolate EC2 (modify security group)
  ├── Revoke IAM credentials
  ├── Block IP in WAF
  ├── Send SNS notification
  └── Create JIRA ticket
```

---

# AWS Security Hub

## What is Security Hub?

AWS Security Hub is a **centralized security findings aggregation and compliance service** that collects findings from GuardDuty, Inspector, Macie, IAM Access Analyzer, Firewall Manager, and third-party tools into a single dashboard.

```text
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  GuardDuty   │ │  Inspector   │ │   Macie      │
│  (Threats)   │ │  (Vulns)     │ │  (Data)      │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
                        ▼
               ┌────────────────┐
               │  Security Hub  │
               │                │
               │  • Dashboard   │
               │  • Standards   │
               │  • Compliance  │
               │  • Automation  │
               └────────────────┘
```

## Security Standards

Security Hub evaluates your environment against pre-built security standards:

| Standard | Focus |
|----------|-------|
| **AWS Foundational Security Best Practices** | AWS-specific security recommendations |
| **CIS AWS Foundations Benchmark** | Center for Internet Security guidelines |
| **PCI DSS** | Payment card industry compliance |
| **NIST 800-53** | US government security framework |

Each standard contains dozens of **controls** that are automatically evaluated and scored.

## Compliance Score

Security Hub provides an overall **security score** (0–100%) based on the percentage of passed controls.

---

## Cross-Account and Cross-Region

Security Hub supports:

- **Multi-account aggregation** via AWS Organizations (delegated administrator)
- **Cross-region aggregation** to a single finding region
- Centralized view of security posture across the entire organization

```text
Account A (us-east-1) ──►
Account B (eu-west-1) ──► Security Hub (Administrator Account)
Account C (ap-south-1) ──►    │
                               ▼
                        Aggregated Dashboard
```

---

## Integration with Other Services

| Source | Finding Type |
|--------|-------------|
| GuardDuty | Threat detection findings |
| Inspector | Vulnerability findings |
| Macie | Sensitive data findings |
| IAM Access Analyzer | Public/cross-account access findings |
| Firewall Manager | Non-compliant WAF/security group findings |
| Config | Non-compliant Config rule findings |
| Third-party tools | Custom findings via ASFF format |

---

# Key Takeaways

- **GuardDuty** is a threat detection service that uses ML and threat intelligence to identify malicious activity.
- GuardDuty analyzes CloudTrail, VPC Flow Logs, DNS Logs, and more — without requiring separate log configuration.
- **Security Hub** aggregates findings from multiple services and evaluates compliance against security standards.
- Use **EventBridge + Lambda** to automate remediation of GuardDuty findings.
- Security Hub provides a **security score** and compliance posture across the organization.
- Both services support **multi-account** deployment via AWS Organizations.
- Enable both services in every account and every region for comprehensive coverage.

---

# Interview Questions

### Q: What data sources does GuardDuty analyze?

CloudTrail events (management + S3 data), VPC Flow Logs, DNS query logs, EKS audit logs, Lambda network activity, and RDS login activity.

### Q: Does GuardDuty require you to enable VPC Flow Logs?

No. GuardDuty independently accesses the data sources — you don't need to enable them separately.

### Q: What is the difference between GuardDuty and Security Hub?

GuardDuty detects threats through analysis. Security Hub aggregates findings from GuardDuty and other services, and evaluates compliance against security standards.

### Q: How do you automate response to GuardDuty findings?

Use EventBridge rules to match specific finding types and trigger Lambda functions for automated remediation (isolate instances, revoke credentials, block IPs).

---
