# AWS Shared Responsibility Model

The AWS Shared Responsibility Model defines the division of security responsibilities between AWS and the customer. AWS is responsible for the security **of** the cloud (infrastructure), while customers are responsible for security **in** the cloud (their data, configurations, and applications).

Understanding this model is essential for every AWS practitioner because it determines who is accountable for each layer of security — and misunderstanding it is one of the most common causes of security incidents in the cloud.

---

# What is the Shared Responsibility Model?

The Shared Responsibility Model is a security framework that clearly delineates:

- **AWS Responsibility** — Security OF the cloud
- **Customer Responsibility** — Security IN the cloud

```text
┌─────────────────────────────────────────────────┐
│             Customer Responsibility             │
│          (Security IN the Cloud)                │
│                                                 │
│  Customer Data                                  │
│  Platform, Applications, IAM                    │
│  Operating System, Network, Firewall Config     │
│  Client-Side Encryption                         │
│  Server-Side Encryption                         │
│  Network Traffic Protection                     │
├─────────────────────────────────────────────────┤
│              AWS Responsibility                 │
│          (Security OF the Cloud)                │
│                                                 │
│  Compute    Storage    Database    Networking    │
│  Hardware / AWS Global Infrastructure           │
│  Regions    Availability Zones    Edge Locations │
│  Physical Security of Data Centers              │
└─────────────────────────────────────────────────┘
```

---

# AWS Responsibility — Security OF the Cloud

AWS manages the security of the underlying infrastructure:

## Physical Security

- Data center access controls (biometric, guards, surveillance)
- Environmental controls (fire suppression, climate control, power redundancy)
- Hardware lifecycle management and secure decommissioning

## Infrastructure

- Global network backbone
- Hypervisor and host operating system security
- Hardware maintenance and patching
- Network infrastructure (routers, switches, load balancers)

## Managed Services Infrastructure

For fully managed services (Lambda, DynamoDB, S3), AWS also manages:

- Operating system patching
- Platform software updates
- Infrastructure scaling

---

# Customer Responsibility — Security IN the Cloud

Customers are responsible for:

## Identity and Access Management

- IAM users, groups, roles, and policies
- Root account protection
- MFA enforcement
- Credential rotation
- Least privilege access

## Data Protection

- Encryption at rest and in transit
- Data classification
- Backup and recovery
- Key management

## Application Security

- Application code security
- Input validation
- Dependency management
- Secrets management

## Network Security

- VPC configuration
- Security group rules
- NACL rules
- VPN and Direct Connect configuration

## Operating System (for IaaS)

- OS patching on EC2 instances
- Firewall configuration
- Antivirus and intrusion detection

---

# How Responsibility Varies by Service Type

The division of responsibility shifts depending on the type of service.

## Infrastructure Services (IaaS)

Example: **Amazon EC2**

```text
Customer Manages:
├── Guest OS patching
├── Security group configuration
├── Application deployment
├── Data encryption
├── IAM roles and policies
└── Network configuration

AWS Manages:
├── Physical servers
├── Hypervisor
├── Network infrastructure
└── Data center security
```

## Container Services (PaaS)

Example: **Amazon RDS**

```text
Customer Manages:
├── Database users and permissions
├── Security group configuration
├── Data encryption settings
├── IAM policies
└── Backup configuration

AWS Manages:
├── OS patching
├── Database engine patching
├── High availability (Multi-AZ)
├── Hardware maintenance
└── Data center security
```

## Abstracted Services (Serverless/SaaS)

Example: **AWS Lambda**

```text
Customer Manages:
├── Function code
├── IAM execution role
├── Environment variables (secrets)
├── VPC configuration (if applicable)
└── Input validation

AWS Manages:
├── Runtime patching
├── Operating system
├── Scaling and availability
├── Compute infrastructure
└── Data center security
```

---

# Responsibility Comparison Table

| Responsibility | EC2 (IaaS) | RDS (PaaS) | Lambda (Serverless) | S3 (Storage) |
|---------------|------------|------------|-------------------|-------------|
| Physical infrastructure | AWS | AWS | AWS | AWS |
| Hypervisor | AWS | AWS | AWS | AWS |
| Operating System | **Customer** | AWS | AWS | AWS |
| Runtime patching | **Customer** | AWS | AWS | AWS |
| Network configuration | **Customer** | **Customer** | **Customer** | **Customer** |
| Firewall (Security Groups) | **Customer** | **Customer** | **Customer** | N/A |
| IAM policies | **Customer** | **Customer** | **Customer** | **Customer** |
| Data encryption | **Customer** | **Customer** | **Customer** | **Customer** |
| Application code | **Customer** | N/A | **Customer** | N/A |
| Backup configuration | **Customer** | **Customer** | N/A | **Customer** |

---

# Common Misconceptions

## "AWS handles all security"

**Incorrect.** AWS secures the infrastructure, but the customer must secure their configurations, data, and applications.

## "If I use a managed service, I have no security responsibilities"

**Incorrect.** Even with Lambda or DynamoDB, customers are responsible for IAM policies, data encryption, and input validation.

## "AWS will notify me if I have a misconfiguration"

**Partially correct.** Services like AWS Config, Trusted Advisor, and IAM Access Analyzer can detect misconfigurations, but they must be enabled and configured by the customer.

## "Compliance certifications mean my application is compliant"

**Incorrect.** AWS infrastructure is certified, but the customer must ensure their own workloads meet compliance requirements.

---

# Real-World Example

An organization deploys a web application on EC2 behind an ALB.

```text
Responsibility Breakdown:

AWS:
├── Physical data center security
├── Network infrastructure
├── Hypervisor security
└── ALB platform availability

Customer:
├── EC2 instance OS patching
├── Application code security
├── Security group rules (ports 80, 443 only)
├── IAM roles for EC2
├── SSL/TLS certificates on ALB
├── Data encryption (EBS, database)
├── VPC and subnet design
└── Monitoring (CloudTrail, GuardDuty)
```

If the customer fails to patch the EC2 operating system and an attacker exploits a known vulnerability, it is the **customer's responsibility** — not AWS's.

---

# Key Takeaways

- The Shared Responsibility Model is the foundation of AWS security.
- AWS secures the infrastructure; customers secure their workloads.
- Responsibility shifts based on service type (IaaS → PaaS → Serverless).
- The more managed a service, the less the customer manages — but the customer always manages IAM, data, and encryption.
- Misunderstanding this model leads to security gaps and compliance failures.
- This is one of the most frequently tested topics in AWS certification exams.

---

# Interview Questions

### Q: What is the AWS Shared Responsibility Model?

A framework that divides security responsibilities between AWS (infrastructure security) and the customer (data, access, and application security).

### Q: Who is responsible for patching an EC2 instance OS?

The customer. EC2 is an IaaS service — the customer manages the guest operating system.

### Q: Who is responsible for patching an RDS database engine?

AWS. RDS is a managed service — AWS handles engine patching during maintenance windows.

### Q: Who is responsible for IAM policies on Lambda?

The customer. Regardless of the service type, the customer always manages IAM.

### Q: Does using a managed service eliminate all security responsibilities?

No. Customers are always responsible for IAM, data encryption, and proper configuration.

---
