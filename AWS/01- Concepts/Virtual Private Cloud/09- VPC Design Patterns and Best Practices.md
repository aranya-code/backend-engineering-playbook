# VPC Design Patterns and Best Practices

This guide covers production-ready VPC design patterns, CIDR planning strategies, multi-account architectures, and operational best practices that senior DevOps engineers and solutions architects use to build secure, scalable, and maintainable network infrastructure on AWS.

VPC design decisions are foundational — they are difficult and sometimes impossible to change after deployment. Getting the design right from the start is critical.

---

# CIDR Planning

## Planning Principles

- **Plan for growth** — allocate larger blocks than you think you need
- **Avoid overlapping CIDRs** — critical for VPC peering, Transit Gateway, and VPN
- **Reserve ranges** — leave room for future VPCs and subnets
- **Document everything** — maintain a central CIDR registry

## Recommended CIDR Strategy

```text
Enterprise CIDR Plan (10.0.0.0/8):

10.0.0.0/12   → Production (16 /16 VPCs)
10.16.0.0/12  → Staging (16 /16 VPCs)
10.32.0.0/12  → Development (16 /16 VPCs)
10.48.0.0/12  → Shared Services (16 /16 VPCs)
10.64.0.0/12  → Reserved for future use
...
172.16.0.0/12 → On-premises networks
```

## Subnet Sizing Guidelines

| Workload | Recommended Size | Usable IPs |
|----------|-----------------|------------|
| ALB / NAT (public) | /24 | 251 |
| Standard workloads | /24 | 251 |
| EKS clusters | /20 – /22 | 1,019 – 4,091 |
| ECS with awsvpc | /22 | 1,019 |
| Lambda (VPC-attached) | /22 | 1,019 |
| Database subnets | /24 | 251 |

---

# Production VPC Design Patterns

## Pattern 1: Three-Tier Web Application

The most common production pattern.

```text
VPC (10.0.0.0/16)
│
├── Public Subnets (10.0.0.0/22 per AZ)
│   ├── Application Load Balancer
│   └── NAT Gateway (one per AZ)
│
├── Private App Subnets (10.0.4.0/22 per AZ)
│   ├── EC2 / ECS / EKS workloads
│   └── Lambda (VPC-attached)
│
├── Private Data Subnets (10.0.8.0/24 per AZ)
│   ├── RDS (Multi-AZ)
│   ├── ElastiCache
│   └── OpenSearch
│
├── VPC Endpoints
│   ├── S3 (Gateway — free)
│   ├── DynamoDB (Gateway — free)
│   ├── Secrets Manager (Interface)
│   ├── ECR (Interface)
│   ├── CloudWatch Logs (Interface)
│   └── SSM (Interface)
│
├── Security Controls
│   ├── Security Groups (per tier, chained)
│   ├── NACLs (subnet-level guardrails)
│   └── Flow Logs (VPC-level → S3 + CloudWatch)
│
└── Connectivity
    ├── Internet Gateway (public subnets)
    └── NAT Gateways (private outbound)
```

---

## Pattern 2: Multi-Account with Shared Services

Enterprise pattern using AWS Organizations.

```text
┌──────────────────────────────────────────────┐
│              Transit Gateway                  │
│              (Central Hub)                    │
└──┬───────────┬───────────┬───────────┬───────┘
   │           │           │           │
   ▼           ▼           ▼           ▼
┌──────┐  ┌──────┐  ┌──────┐  ┌──────────────┐
│ Prod │  │ Dev  │  │ Stg  │  │ Shared Svcs  │
│ VPC  │  │ VPC  │  │ VPC  │  │ VPC          │
│      │  │      │  │      │  │ ├── DNS      │
│ 10.0 │  │ 10.16│  │ 10.32│  │ ├── AD      │
│      │  │      │  │      │  │ ├── CI/CD    │
│      │  │      │  │      │  │ └── Logging  │
└──────┘  └──────┘  └──────┘  └──────────────┘
   │                                   │
   ▼                                   ▼
On-Premises ═══════════════════ VPN / Direct Connect
```

TGW route tables enforce segmentation:
- Production can access Shared Services and on-premises
- Development can access Shared Services only
- No cross-environment access (prod ↛ dev)

---

## Pattern 3: Private-Only VPC (No Internet)

For highly sensitive workloads with no internet connectivity requirement.

```text
VPC (No Internet Gateway, No NAT Gateway)
│
├── Private Subnets only
│   ├── EC2 / ECS workloads
│   └── RDS databases
│
├── VPC Endpoints (all access via endpoints)
│   ├── S3, DynamoDB (Gateway)
│   ├── ECR, Secrets Manager, SSM, STS (Interface)
│   ├── CloudWatch Logs, KMS (Interface)
│   └── Any other required services
│
└── Connectivity
    └── Transit Gateway or VPN (to other VPCs / on-premises)
```

---

# Multi-AZ Best Practices

- Deploy **every tier** across at least 2 AZs (preferably 3)
- Deploy **one NAT Gateway per AZ** for HA
- Use **AZ-independent subnets** — each AZ has its own route table
- Deploy **RDS Multi-AZ** for database failover
- Use **ALB** (automatically multi-AZ) for traffic distribution

```text
AZ Failure Impact Without Multi-AZ NAT:

AZ-1 NAT fails → AZ-2 instances lose internet
                  (if sharing AZ-1 NAT)

AZ Failure Impact With Multi-AZ NAT:

AZ-1 NAT fails → Only AZ-1 instances affected
AZ-2 NAT       → AZ-2 instances continue normally
```

---

# Cost Optimization

| Cost Driver | Optimization |
|-------------|-------------|
| NAT Gateway ($32/month + data) | Use VPC Endpoints for S3/DynamoDB traffic |
| NAT Gateway data processing | Consolidate outbound traffic patterns |
| Interface Endpoints ($7.20/month each) | Share endpoints via Transit Gateway |
| VPC Peering data transfer | Free within same AZ, charged cross-AZ |
| Transit Gateway ($0.05/hr per attachment) | Consolidate VPCs where possible |
| Direct Connect | Use reserved capacity for predictable workloads |

---

# Operational Best Practices

| Category | Practice |
|----------|---------|
| **Naming** | Use consistent naming: `prod-web-public-1a`, `dev-app-private-1b` |
| **Tagging** | Tag all VPC resources: Environment, Team, CostCenter |
| **Documentation** | Maintain CIDR allocation registry and network diagrams |
| **IaC** | Define all VPC infrastructure in CloudFormation or Terraform |
| **Monitoring** | Enable Flow Logs, CloudWatch alarms on NAT Gateway metrics |
| **Security** | Regular security group audits, Config rules for compliance |
| **DNS** | Use Route 53 private hosted zones for internal service discovery |
| **Automation** | Use AWS Config to detect and remediate non-compliant network configs |

---

# Common Mistakes to Avoid

| Mistake | Impact | Solution |
|---------|--------|----------|
| Using default VPC for production | Permissive defaults, poor isolation | Always create custom VPCs |
| CIDR blocks too small | Cannot add instances, EKS runs out of IPs | Plan for growth (/20 or larger for EKS) |
| Overlapping CIDRs | Cannot peer, cannot use TGW | Maintain a CIDR registry |
| Single NAT Gateway | AZ failure takes down all private outbound | Deploy NAT per AZ |
| No VPC Endpoints | Unnecessary NAT costs, security exposure | Always deploy S3/DynamoDB gateway endpoints |
| Security groups referencing CIDRs | Brittle, hard to maintain | Reference other SGs |
| No Flow Logs | No network visibility, compliance gaps | Enable at VPC level |
| No DNS resolution | Cannot use private hosted zones | Enable DNS hostnames and resolution |

---

# Key Takeaways

- Plan CIDRs carefully — overlapping ranges prevent VPC connectivity.
- Use the three-tier pattern (public/private-app/private-data) for most workloads.
- Deploy NAT Gateways per AZ for high availability.
- Use VPC Endpoints to reduce cost and improve security.
- Transit Gateway scales better than VPC Peering for enterprise architectures.
- Private-only VPCs (no IGW) provide the highest security for sensitive workloads.
- Define all networking with Infrastructure as Code — VPC changes are high-risk manual operations.

---
