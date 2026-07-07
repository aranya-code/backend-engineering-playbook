# VPC Security

VPC (Virtual Private Cloud) security encompasses the network-level controls that protect AWS resources from unauthorized access and network-based attacks. These controls include Security Groups, Network ACLs, VPC Endpoints, Flow Logs, and network architecture patterns that together create a defense-in-depth network security posture.

VPC security is the foundation of infrastructure protection in AWS — misconfigured network controls are one of the most common causes of security incidents.

---

# Security Groups

Security Groups act as **stateful virtual firewalls** at the instance (ENI) level, controlling inbound and outbound traffic.

## Key Characteristics

- **Stateful** — return traffic is automatically allowed
- Operate at the **instance level** (attached to ENIs)
- Support **allow rules only** — no deny rules
- All rules are evaluated before deciding (no ordering)
- Default: all inbound denied, all outbound allowed

```text
Internet
    │
    ▼
┌──────────────────────┐
│    Security Group     │
│                       │
│  Inbound Rules:       │
│  ├── Port 443 from 0.0.0.0/0  │
│  └── Port 22 from 10.0.0.0/16 │
│                       │
│  Outbound Rules:      │
│  └── All traffic allowed       │
│                       │
│  ┌─────────────┐     │
│  │  EC2 / ENI  │     │
│  └─────────────┘     │
└──────────────────────┘
```

## Best Practices

- Use **least privilege** — open only required ports
- Reference other **security groups** as sources instead of CIDR ranges
- Never open port 22 (SSH) to 0.0.0.0/0 — use SSM Session Manager
- Create separate security groups per tier (web, app, data)
- Use descriptive names and tags

---

# Network ACLs (NACLs)

Network ACLs are **stateless firewalls** at the subnet level.

## Key Characteristics

- **Stateless** — return traffic must be explicitly allowed
- Operate at the **subnet level**
- Support both **allow and deny rules**
- Rules are evaluated **in order** (lowest number first)
- Default NACL: all traffic allowed

```text
Internet
    │
    ▼
┌──────────────────────────┐
│     Network ACL           │
│                           │
│  Rule 100: ALLOW 443 IN  │
│  Rule 200: DENY  22  IN  │
│  Rule *:   DENY ALL  IN  │
│                           │
│  Rule 100: ALLOW 1024-65535 OUT  │
│  Rule *:   DENY ALL  OUT │
│                           │
│  ┌──────────────────┐    │
│  │     Subnet       │    │
│  │  ┌────┐  ┌────┐  │    │
│  │  │EC2 │  │EC2 │  │    │
│  │  └────┘  └────┘  │    │
│  └──────────────────┘    │
└──────────────────────────┘
```

## Ephemeral Ports

Because NACLs are stateless, outbound rules must allow **ephemeral ports** (1024–65535) for return traffic from clients.

---

# Security Groups vs NACLs

| Feature | Security Groups | NACLs |
|---------|----------------|-------|
| **Level** | Instance (ENI) | Subnet |
| **Statefulness** | Stateful | Stateless |
| **Rule types** | Allow only | Allow and Deny |
| **Rule evaluation** | All rules evaluated | Rules evaluated in order |
| **Default inbound** | Deny all | Allow all (default NACL) |
| **Default outbound** | Allow all | Allow all (default NACL) |
| **Return traffic** | Automatically allowed | Must be explicitly allowed |
| **Use case** | Fine-grained instance control | Subnet-level guardrails |

## When to Use Each

- **Security Groups**: Primary tool for traffic control. Use for every resource.
- **NACLs**: Additional subnet-level guardrails. Use to block known malicious IPs or as a compliance backstop.

---

# VPC Endpoints

VPC Endpoints allow private connectivity to AWS services without traversing the public internet.

## Gateway Endpoints

- Support **S3** and **DynamoDB** only
- Free
- Route table entry points to the service
- No ENI required

## Interface Endpoints (AWS PrivateLink)

- Support **100+ AWS services**
- Creates an ENI in your subnet with a private IP
- Costs: $0.01/hour per endpoint + data processing
- DNS resolution via private hosted zones
- Supports security groups

```text
Without VPC Endpoint:           With VPC Endpoint:

EC2 ──► NAT GW ──► IGW         EC2 ──► VPC Endpoint
         │                              │
         ▼                              ▼
      Internet                     AWS Service
         │                      (Private Network)
         ▼
    AWS Service
```

## Why VPC Endpoints Matter for Security

- Data never traverses the public internet
- Reduces attack surface
- Meets compliance requirements for private connectivity
- Can be restricted with endpoint policies

---

# VPC Flow Logs

VPC Flow Logs capture information about IP traffic going to and from network interfaces in your VPC.

## Capture Levels

| Level | What is Captured |
|-------|-----------------|
| **VPC** | All traffic in the entire VPC |
| **Subnet** | All traffic in a specific subnet |
| **ENI** | Traffic for a specific network interface |

## Flow Log Record Format

```text
version account-id interface-id srcaddr dstaddr srcport dstport protocol packets bytes start end action log-status
```

Example:

```text
2 123456789012 eni-abc123 10.0.0.1 52.94.76.5 49152 443 6 10 5000 1625000000 1625000060 ACCEPT OK
```

## Destinations

- **CloudWatch Logs** — for real-time analysis and metric filters
- **Amazon S3** — for long-term storage and batch analysis
- **Kinesis Data Firehose** — for streaming to analytics tools

## Security Use Cases

- Detect unauthorized access attempts
- Monitor rejected traffic patterns
- Identify data exfiltration (unusual outbound traffic)
- Compliance auditing
- Troubleshoot connectivity issues

---

# Bastion Hosts vs SSM Session Manager

## Bastion Host (Traditional)

- EC2 instance in a public subnet
- SSH/RDP jump box to private instances
- Requires port 22 open, key management
- Security risk: exposed to internet

## SSM Session Manager (Recommended)

- No open inbound ports required
- No SSH keys to manage
- IAM-based access control
- Session logging to S3/CloudWatch
- Works through VPC endpoints (no internet needed)

```text
Bastion:                    SSM Session Manager:

User ──► Bastion (port 22)  User ──► AWS Console/CLI
              │                        │
              ▼                        ▼ (HTTPS)
         Private EC2             SSM Agent on EC2
                                 (No inbound ports)
```

| Feature | Bastion Host | SSM Session Manager |
|---------|-------------|-------------------|
| Inbound ports | Port 22/3389 required | None |
| Key management | SSH keys | IAM |
| Audit logging | Manual | Built-in (S3, CloudWatch) |
| Internet access | Required for bastion | Optional (VPC endpoint) |
| Cost | EC2 instance cost | Free (SSM agent) |
| Security | Higher risk | Lower risk |

---

# Network Security Architecture

```text
┌─────────────────────────────────────────────────┐
│                      VPC                         │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │           Public Subnet                   │   │
│  │  NACL: Allow 80, 443 IN                  │   │
│  │                                           │   │
│  │  ┌──────────────┐                        │   │
│  │  │     ALB      │  SG: Allow 443 from    │   │
│  │  │              │      0.0.0.0/0         │   │
│  │  └──────┬───────┘                        │   │
│  └─────────┼────────────────────────────────┘   │
│            │                                     │
│  ┌─────────┼────────────────────────────────┐   │
│  │         ▼    Private Subnet (App)         │   │
│  │  NACL: Allow traffic from public subnet   │   │
│  │                                           │   │
│  │  ┌──────────────┐                        │   │
│  │  │  EC2 / ECS   │  SG: Allow 8080 from  │   │
│  │  │  Application │      ALB SG only      │   │
│  │  └──────┬───────┘                        │   │
│  └─────────┼────────────────────────────────┘   │
│            │                                     │
│  ┌─────────┼────────────────────────────────┐   │
│  │         ▼    Private Subnet (Data)        │   │
│  │  NACL: Allow traffic from app subnet      │   │
│  │                                           │   │
│  │  ┌──────────────┐                        │   │
│  │  │     RDS      │  SG: Allow 5432 from  │   │
│  │  │  Database    │      App SG only      │   │
│  │  └──────────────┘                        │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  VPC Endpoints: S3 (Gateway), Secrets Manager    │
│  Flow Logs: Enabled → S3 + CloudWatch            │
└─────────────────────────────────────────────────┘
```

---

# Key Takeaways

- **Security Groups** are stateful, instance-level firewalls — your primary traffic control tool.
- **NACLs** are stateless, subnet-level firewalls — use as additional guardrails.
- **VPC Endpoints** eliminate internet exposure for AWS service access.
- **Flow Logs** provide network traffic visibility for security monitoring and compliance.
- **SSM Session Manager** replaces bastion hosts for secure, keyless instance access.
- Reference security groups (not CIDRs) for intra-VPC rules to create dynamic, maintainable policies.
- Design networks in tiers: public (ALB), private app, private data — with SG chaining between tiers.

---

# Interview Questions

### Q: What is the difference between Security Groups and NACLs?

Security Groups are stateful, instance-level, allow-only firewalls. NACLs are stateless, subnet-level, support allow and deny rules, and evaluate rules in order.

### Q: Why are NACLs stateless?

NACLs evaluate each packet independently. If you allow inbound traffic on port 443, you must also allow outbound traffic on ephemeral ports (1024–65535) for the response.

### Q: What is a VPC Endpoint?

A VPC Endpoint enables private connectivity to AWS services without traversing the public internet. Gateway endpoints support S3/DynamoDB; Interface endpoints support 100+ services.

### Q: Why is SSM Session Manager preferred over bastion hosts?

SSM requires no open inbound ports, no SSH key management, provides IAM-based access control, built-in session logging, and can work entirely over private connectivity.

---
