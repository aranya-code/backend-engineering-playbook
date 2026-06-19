# ☁️ AWS Knowledge Base

A structured personal AWS knowledge base built for interview preparation, certification study, and real-world cloud engineering reference. Covers core AWS services with concept deep-dives, architecture patterns, CLI references, interview Q&A, exam cheat sheets, and documented troubleshooting.

---

## 📁 Repository Structure

```
AWS/
├── concepts/
│   ├── EC2/                        # Compute, storage, networking, scaling
│   ├── IAM/                        # Identity, policies, roles, security
│   ├── Amazon S3/                  # 19-topic S3 deep-dive series
│   ├── Database/                   # RDS, ElastiCache, MemoryDB
│   ├── CloudFront/                 # 13-part CDN series
│   ├── Route 53/                   # DNS and traffic routing
│   ├── Virtual_Private_Cloud/      # VPC networking fundamentals
│   ├── AWS-Architecture/           # Cross-service architecture patterns
│   └── AWS-Security/               # Auth and signing mechanisms
├── cli/
│   ├── Basics/                     # AWS CLI setup and configuration
│   └── IAM/                        # IAM CLI commands
├── troubleshooting/
│   └── AWS-Troubleshooting.md
├── images/                         # Screenshots and diagrams
└── README.md
```

---

## 📚 Topics Covered

### 🖥️ EC2

| Category | Files |
|----------|-------|
| **Fundamentals** | [EC2 Basics](concepts/EC2/EC2%20Basics.md), [Instance Types](concepts/EC2/Instance%20Types.md), [Purchasing Options](concepts/EC2/Purchasing%20Options.md), [Instance Metadata](concepts/EC2/EC2-Instance-Metadata.md) |
| **Storage** | [EBS](concepts/EC2/Storage/EBS.md), [EBS Snapshot](concepts/EC2/Storage/EBS%20Snapshot.md), [EBS Multi-Attach](concepts/EC2/Storage/EBS%20Multi-Attach.md), [Instance Store](concepts/EC2/Storage/Instance%20Store.md), [EFS](concepts/EC2/Storage/EFS.md), [Amazon EFS](concepts/EC2/Storage/Amazon%20EFS.md), [IOPS](concepts/EC2/Storage/IOPS.md) |
| **Networking** | [Security Groups](concepts/EC2/Networking/Security%20Groups.md), [NACL vs SG](concepts/EC2/Networking/NACL%20vs%20SG.md), [Elastic IP](concepts/EC2/Networking/Elastic%20IP.md), [Ports](concepts/EC2/Networking/Ports.md) |
| **Access** | [SSH](concepts/EC2/Access/SSH.md), [Key Pairs](concepts/EC2/Access/Key%20Pairs.md), [User Data](concepts/EC2/Access/User%20Data.md) |
| **Load Balancing** | [Elastic Load Balancer](concepts/EC2/Load%20Balancing/Elastic%20Load%20Balancer.md), [Load Balancer Types](concepts/EC2/Load%20Balancing/Load%20Balancer%20Types.md), [SSL Certificates](concepts/EC2/Load%20Balancing/SSL%20Certificates.md), [SNI](concepts/EC2/Load%20Balancing/SNI.md), [Sticky Sessions](concepts/EC2/Load%20Balancing/Sticky%20Sessions.md) |
| **Auto Scaling** | [Auto Scaling Groups](concepts/EC2/AutoScaling/Auto_Scaling_Groups.md) |
| **Troubleshooting** | [Connection Timeout](concepts/EC2/Troubleshooting/Connection%20Timeout.md), [Connection Refused](concepts/EC2/Troubleshooting/Connection%20Refused.md) |
| **Interview** | [EC2 Interview Questions](concepts/EC2/Interview/EC2%20Interview%20Questions.md), [Quick Revision](concepts/EC2/Interview/Quick%20Revision.md) |

---

### 🔐 IAM

| Category | Files |
|----------|-------|
| **Fundamentals** | [IAM Basics](concepts/IAM/IAM%20Basics.md), [Users vs Groups vs Roles](concepts/IAM/Users%20vs%20Groups%20vs%20Roles.md) |
| **Policies** | [Policy Basics](concepts/IAM/Policies/Policy%20Basics.md), [Policy Structure](concepts/IAM/Policies/IAM%20Policy%20Structure.md), [Inline vs Managed](concepts/IAM/Policies/Inline%20vs%20Managed%20Policies.md), [Policy Examples](concepts/IAM/Policies/Policy%20Examples.md) |
| **Roles** | [IAM Roles](concepts/IAM/Roles/IAM%20Roles.md), [EC2 Roles](concepts/IAM/Roles/EC2%20Roles.md), [Assume Role](concepts/IAM/Roles/Assume%20Role.md) |
| **Security** | [MFA](concepts/IAM/Security/MFA.md), [Root Account Best Practices](concepts/IAM/Security/Root%20Account%20Best%20Practices.md), [Least Privilege](concepts/IAM/Security/Least%20Privilege.md), [Credential Rotation](concepts/IAM/Security/Credential%20Rotation.md) |
| **Monitoring** | [Credentials Report](concepts/IAM/Monitoring/IAM%20Credentials%20Report.md), [Access Advisor](concepts/IAM/Monitoring/IAM%20Access%20Advisor.md) |
| **Troubleshooting** | [Access Denied](concepts/IAM/Troubleshooting/Access%20Denied.md), [STS AssumeRole Errors](concepts/IAM/Troubleshooting/STS%20AssumeRole%20Errors.md) |
| **Interview** | [IAM Interview Questions](concepts/IAM/Interview/IAM%20Interview%20Questions.md), [Quick Revision](concepts/IAM/Interview/Quick%20Revision.md) |

---

### 🗄️ Amazon S3 (19-topic deep-dive)

Each sub-topic follows a consistent structure: overview → CLI examples → production scenarios → interview Q&A → exam cheat sheet.

| Sub-topic | Files |
|-----------|-------|
| **Fundamentals** | [What is S3](concepts/Amazon%20S3/S3%20Fundamentals/01-What-is-S3.md), [Buckets](concepts/Amazon%20S3/S3%20Fundamentals/02-Buckets.md), [Objects](concepts/Amazon%20S3/S3%20Fundamentals/03-Objects.md), [Object Keys & Prefixes](concepts/Amazon%20S3/S3%20Fundamentals/04-Object-Keys-and-Prefixes.md), [S3 Limits & Exam Facts](concepts/Amazon%20S3/S3%20Fundamentals/05-S3-Limits-and-Exam-Facts.md) |
| **Security** | IAM vs Bucket Policies, Bucket Policies, ACLs, Block Public Access, Access Points, Policy Evaluation Logic |
| **Versioning & Data Protection** | Versioning, Delete Markers, MFA Delete, Object Lock, Legal Hold & Retention, Recovery Scenarios |
| **Storage Classes** | Standard, Standard-IA, One Zone-IA, Intelligent-Tiering, Glacier Instant/Flexible/Deep Archive, Cost Comparison |
| **Lifecycle Policies** | Transition Actions, Expiration Actions, Versioned Object Lifecycle, Cost Optimization Strategies |
| **Encryption** | SSE-S3, SSE-KMS, SSE-C, Client-Side Encryption, KMS Deep Dive, Envelope Encryption, Encryption In Transit |
| **Replication** | CRR (Cross-Region), SRR (Same-Region), Delete Marker Replication, RTC, Multi-Account Replication |
| **Static Website Hosting** | Configuration, Index/Error Documents, Bucket Policies, Custom Domains, Route 53 & CloudFront Integration |
| **Presigned URLs** | Overview, Upload & Download URLs, Security Considerations, Expiration & Access Control |
| **Transfer Acceleration** | Overview, How It Works, Edge Locations, Performance Benefits, Cost Considerations |
| **Event Notifications** | Supported Events, SQS Integration, SNS Integration, Lambda Integration, Event-Driven Architectures |
| **Access Points** | Overview, VPC Access Points, Multi-Team Access Design, Access Point Policies |
| **Object Lock Advanced** | Governance Mode, Compliance Mode, Legal Hold, WORM Storage, Regulatory Compliance |
| **Multi-Region Access Points** | Global Endpoint Architecture, Traffic Routing, Failover & Resilience, Active-Active Architectures |
| **Storage Lens & Inventory** | Metrics & Dashboards, Organization-Level Visibility, Inventory Reports, Cost Optimization Insights |
| **Performance** | [S3 Performance & Events](concepts/Amazon%20S3/S3%20Performance/S3-Performance-and-Events.md) |
| **Interview Questions** | Beginner, Intermediate, Advanced, Scenario-Based, Architecture, Security, Cost Optimization, Troubleshooting |
| **Cheat Sheets** | One-Page S3, Storage Classes, Security, Versioning & Replication, Encryption, Lifecycle, Architecture Patterns |
| **Exam Guide** | Exam Strategy, Frequently Tested Concepts, Decision Guides, Common Exam Traps, Memory Tricks |

---

### 🗃️ Databases

| Service | Files |
|---------|-------|
| **RDS** | [Overview](concepts/Database/RDS/RDS_Overview.md), [Read Replicas](concepts/Database/RDS/RDS_Read_Replicas.md), [Multi-AZ](concepts/Database/RDS/RDS_Multi_AZ.md), [RDS Proxy](concepts/Database/RDS/RDS_Proxy.md), [Security](concepts/Database/RDS/RDS_Security.md), [Storage AutoScaling](concepts/Database/RDS/RDS_Storage_AutoScaling.md) |
| **ElastiCache** | [Overview](concepts/Database/ElastiCache/ElastiCache_Overview.md), [Caching Strategies](concepts/Database/ElastiCache/Caching_Strategies.md) |
| **MemoryDB** | [MemoryDB for Redis](concepts/Database/MemoryDB/MemoryDB_for_Redis.md) |
| **Quick Revision** | [Database Quick Revision Notes](concepts/Database/Quick_Revision_Notes.md) |

---

### 🌐 CloudFront (13-part series)

| # | Topic |
|---|-------|
| 1 | [Introduction](concepts/CloudFront/1.%20Introduction.md) |
| 2 | [Architecture](concepts/CloudFront/2.%20Architecture.md) |
| 3 | [Origins](concepts/CloudFront/3.%20Origins.md) |
| 4 | [Caching](concepts/CloudFront/4.%20Caching.md) |
| 5 | [Cache Keys and Policies](concepts/CloudFront/5.%20Cache%20Keys%20and%20Policies.md) |
| 6 | [Security](concepts/CloudFront/6.%20Security.md) |
| 7 | [Signed URLs and Signed Cookies](concepts/CloudFront/7.%20Signed%20URLs%20and%20Signed%20Cookies.md) |
| 8 | [Edge Computing](concepts/CloudFront/8.%20Edge%20Computing.md) |
| 9 | [Monitoring and Logging](concepts/CloudFront/9.%20Monitoring%20and%20Logging.md) |
| 10 | [Best Practices](concepts/CloudFront/10.%20Best%20Practices.md) |
| 11 | [Troubleshooting](concepts/CloudFront/11.%20Troubleshooting.md) |
| 12 | [Real-World Scenarios](concepts/CloudFront/12.%20Real-World%20Scenarios.md) |
| 13 | [Interview Questions and Answers](concepts/CloudFront/13.%20Interview%20Questions%20and%20Answers.md) |

---

### 🌍 Route 53

| File |
|------|
| [Route 53 — DNS, routing policies, health checks, failover, traffic management](concepts/Route%2053/Route53.md) |

---

### 🔒 VPC (Virtual Private Cloud)

| File | Topic |
|------|-------|
| [VPC](concepts/Virtual_Private_Cloud/VPC.md) | Core VPC concept |
| [Subnets](concepts/Virtual_Private_Cloud/Subnets.md) | Public and private subnets |
| [Route Tables](concepts/Virtual_Private_Cloud/Route-Tables.md) | Traffic routing rules |
| [Internet Gateway](concepts/Virtual_Private_Cloud/Internet-Gateway.md) | Public internet access |
| [NAT Gateway](concepts/Virtual_Private_Cloud/NAT-Gateway.md) | Outbound internet for private subnets |
| [Security Groups](concepts/Virtual_Private_Cloud/Security-Groups.md) | Instance-level firewall |
| [Network ACLs](concepts/Virtual_Private_Cloud/Network-ACLs.md) | Subnet-level firewall |
| [SG vs NACL](concepts/Virtual_Private_Cloud/SecurityGroup-vs-NACL.md) | Side-by-side comparison |
| [VPC Peering](concepts/Virtual_Private_Cloud/VPC-Peering.md) | Cross-VPC connectivity |
| [VPC Endpoints](concepts/Virtual_Private_Cloud/VPC-Endpoints.md) | Private AWS service access |
| [VPC Flow Logs](concepts/Virtual_Private_Cloud/VPC-Flow-Logs.md) | Network traffic logging |
| [Site-to-Site VPN](concepts/Virtual_Private_Cloud/Site-to-Site-VPN.md) | On-premises connectivity |
| [Direct Connect](concepts/Virtual_Private_Cloud/Direct-Connect.md) | Dedicated private connection to AWS |

---

### 🏗️ Architecture & Security Patterns

| File | Topic |
|------|-------|
| [Exponential Backoff Strategy](concepts/AWS-Architecture/Exponential-Backoff-Strategy.md) | Retry mechanism for API throttling — doubling wait times, jitter, ThrottlingException handling |
| [AWS Signature vs SigV4](concepts/AWS-Security/AWS-Signature-vs-SigV4.md) | HMAC-SHA256 signing, SigV2 deprecation, region-specific validation |
| [EC2 Instance Metadata](concepts/EC2/EC2-Instance-Metadata.md) | IMDSv1 vs IMDSv2, SSRF protection, credential retrieval |

---

### 💻 CLI Reference

| File | Topic |
|------|-------|
| [AWS CLI Basics](cli/Basics/AWS-CLI-Basics.md) | Version check, `aws configure`, access key setup |
| [IAM CLI](cli/IAM/IAM.md) | `aws iam list-users` and IAM CLI commands |

---

### 🔧 Troubleshooting

| # | Problem | Root Cause | Fix |
|---|---------|------------|-----|
| 1 | Root EBS volume detach failure | Cannot detach root volume from a running instance | Stop the instance first; force stop if stuck in "Stopping" |

Each troubleshooting entry includes: error message, root cause analysis, step-by-step resolution, CLI verification commands, and an exam/interview quick-reference summary.

---

## 🎯 Note Structure

Every topic in this repo follows a deliberate format:

- **Definition** — What the service/feature is
- **Why it exists** — The problem it solves
- **How it works** — Architecture and mechanics
- **Real-world scenarios** — Production patterns
- **CLI examples** — Hands-on commands
- **Interview Q&A** — Common questions with answers
- **Exam cheat sheet** — Last-minute revision

---

## 📌 Issues Found in the Existing README

The root `README.md` lists several services in the **Future Topics** section that are already documented in this repo:

| Listed as "Future" | Actually Present |
|--------------------|-----------------|
| Route 53 | ✅ `concepts/Route 53/Route53.md` |
| VPC Deep Dive | ✅ `concepts/Virtual_Private_Cloud/` (13 files) |

These sections should be moved from "Future Topics" into the main topics list.

---

*Created by Aranya Majumdar*
