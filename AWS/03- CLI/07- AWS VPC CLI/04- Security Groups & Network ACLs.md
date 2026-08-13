# Security Groups & Network ACLs

> Learn how Amazon VPC secures network traffic using Security Groups (SGs) and Network Access Control Lists (NACLs). This chapter covers inbound and outbound rules, stateful vs stateless firewalls, rule evaluation, AWS CLI commands, and production security best practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Security Groups
- Understand Network ACLs
- Configure inbound and outbound rules
- Compare stateful and stateless firewalls
- Manage Security Groups using AWS CLI
- Manage Network ACLs using AWS CLI
- Design secure production VPCs

---

# Network Security Layers

Amazon VPC provides multiple layers of security.

```text
Internet
     │
     ▼
Internet Gateway
     │
     ▼
Network ACL
     │
     ▼
Subnet
     │
     ▼
Security Group
     │
     ▼
EC2 Instance
```

Network ACLs secure the subnet.

Security Groups secure the instance.

---

# Security Groups

A Security Group acts as a **virtual firewall** for EC2 instances and other AWS resources.

It controls:

- Incoming traffic
- Outgoing traffic

Security Groups are attached to resources, not subnets.

---

# Security Group Architecture

```text
Internet

↓

Security Group

↓

EC2
```

Only traffic allowed by the Security Group reaches the instance.

---

# Security Group Characteristics

Security Groups are:

- Stateful
- Instance-level
- Allow rules only
- Default deny

---

# Stateful Firewall

Security Groups are stateful.

Example:

```text
Client

↓

Request Allowed

↓

EC2

↓

Response Automatically Allowed
```

You do **not** need separate outbound rules for responses.

---

# Default Security Group

Every VPC contains a default Security Group.

Characteristics:

- Allows traffic from itself
- Allows all outbound traffic
- Blocks unsolicited inbound traffic

Production workloads typically use custom Security Groups.

---

# Create a Security Group

```bash
aws ec2 create-security-group \
--group-name web-sg \
--description "Web Server Security Group" \
--vpc-id vpc-0123456789abcdef0
```

---

# List Security Groups

```bash
aws ec2 describe-security-groups
```

---

# Describe a Security Group

```bash
aws ec2 describe-security-groups \
--group-ids sg-0123456789abcdef0
```

---

# Delete a Security Group

```bash
aws ec2 delete-security-group \
--group-id sg-0123456789abcdef0
```

Cannot delete if attached to resources.

---

# Allow SSH Access

```bash
aws ec2 authorize-security-group-ingress \
--group-id sg-0123456789abcdef0 \
--protocol tcp \
--port 22 \
--cidr 203.0.113.10/32
```

Allow SSH only from a trusted IP.

---

# Allow HTTP

```bash
aws ec2 authorize-security-group-ingress \
--group-id sg-0123456789abcdef0 \
--protocol tcp \
--port 80 \
--cidr 0.0.0.0/0
```

---

# Allow HTTPS

```bash
aws ec2 authorize-security-group-ingress \
--group-id sg-0123456789abcdef0 \
--protocol tcp \
--port 443 \
--cidr 0.0.0.0/0
```

---

# Remove a Rule

```bash
aws ec2 revoke-security-group-ingress
```

Removes an existing inbound rule.

---

# Security Group Example

```text
Web Server

Inbound

22 → Admin IP

80 → Internet

443 → Internet

Outbound

All Traffic
```

---

# Security Group Referencing

Security Groups can reference other Security Groups.

Example:

```text
Internet

↓

Web Security Group

↓

Application Security Group

↓

Database Security Group
```

Instead of allowing IP addresses, you allow trusted resources.

---

# Database Example

```text
Database

↓

Accept MySQL

↓

Only from Application Security Group
```

The database remains inaccessible from the Internet.

---

# Network ACL (NACL)

A Network ACL is a firewall operating at the **subnet level**.

Every subnet must be associated with one Network ACL.

---

# NACL Architecture

```text
Internet

↓

Network ACL

↓

Subnet

↓

EC2
```

---

# NACL Characteristics

Network ACLs are:

- Stateless
- Subnet-level
- Allow and Deny rules
- Numbered rules

---

# Stateless Firewall

Unlike Security Groups:

```text
Request

↓

Allowed

↓

Response

↓

Must also be allowed
```

Both inbound and outbound rules must be configured.

---

# Default Network ACL

The default NACL:

- Allows all inbound traffic
- Allows all outbound traffic

Custom NACLs should be used for production environments.

---

# Create a Network ACL

```bash
aws ec2 create-network-acl \
--vpc-id vpc-0123456789abcdef0
```

---

# List Network ACLs

```bash
aws ec2 describe-network-acls
```

---

# Delete a Network ACL

```bash
aws ec2 delete-network-acl \
--network-acl-id acl-0123456789abcdef0
```

---

# Associate NACL with Subnet

```bash
aws ec2 replace-network-acl-association
```

Associates a different NACL with a subnet.

---

# Add an Inbound Rule

Example:

```bash
aws ec2 create-network-acl-entry \
--network-acl-id acl-0123456789abcdef0 \
--rule-number 100 \
--protocol tcp \
--port-range From=80,To=80 \
--cidr-block 0.0.0.0/0 \
--rule-action allow \
--ingress
```

---

# Add an Outbound Rule

Configure a corresponding outbound rule.

Remember:

NACLs are **stateless**.

---

# Rule Evaluation

Rules are evaluated in ascending order.

```text
100

↓

110

↓

120

↓

*

```

The first matching rule is applied.

---

# Security Groups vs Network ACLs

| Feature | Security Group | Network ACL |
|----------|---------------|-------------|
| Level | Instance | Subnet |
| Stateful | Yes | No |
| Allow Rules | Yes | Yes |
| Deny Rules | No | Yes |
| Rule Order | No | Yes |
| Default | Deny Inbound | Allow Inbound |

---

# Typical Production Design

```text
Internet

↓

ALB

↓

Web SG

↓

Application SG

↓

Database SG

────────────

Public Subnet

↓

Public NACL

────────────

Private Subnet

↓

Private NACL
```

Security Groups protect resources.

NACLs provide subnet-level protection.

---

# Common Errors

## InvalidGroup.NotFound

Verify:

- Security Group ID
- Region
- AWS Account

---

## DependencyViolation

Security Group is attached to:

- EC2
- ALB
- Lambda ENI
- ECS

Detach resources first.

---

## RulesPerSecurityGroupLimitExceeded

Maximum Security Group rule limit reached.

Consider:

- Using Security Group references
- Consolidating rules

---

## NetworkAclEntryAlreadyExists

The rule number already exists.

Choose another rule number.

---

# Production Best Practices

- Never allow SSH from `0.0.0.0/0`.
- Restrict RDP access.
- Keep databases in private subnets.
- Use Security Group references instead of IP addresses.
- Use separate Security Groups for each application tier.
- Use custom NACLs for production.
- Apply least-privilege network access.
- Review firewall rules regularly.

---

# Real-World Workflow

```text
Create VPC

↓

Create Subnets

↓

Create Security Groups

↓

Create Network ACLs

↓

Deploy EC2

↓

Associate Security Groups

↓

Associate Network ACLs

↓

Production
```

---

# Architecture Note

```text
Internet
      │
      ▼
Internet Gateway
      │
      ▼
Network ACL
      │
      ▼
Subnet
      │
      ▼
Security Group
      │
      ▼
EC2 Instance
```

Security Groups and Network ACLs complement each other rather than replace one another.

---

# Interview Note

### Question

**What is the difference between a Security Group and a Network ACL?**

### Answer

A **Security Group** is a stateful virtual firewall that operates at the instance level. It only supports allow rules, and return traffic is automatically permitted. A **Network ACL (NACL)** is a stateless firewall that operates at the subnet level. It supports both allow and deny rules, evaluates rules in numerical order, and requires explicit rules for both inbound and outbound traffic. In production, Security Groups provide fine-grained protection for individual resources, while NACLs provide an additional layer of subnet-level security.

---

# Key Takeaways

- Security Groups protect AWS resources at the instance level.
- Network ACLs protect entire subnets.
- Security Groups are stateful; Network ACLs are stateless.
- Security Groups support only allow rules.
- Network ACLs support both allow and deny rules.
- Use Security Group references to simplify network security.
- Combining Security Groups and Network ACLs provides layered network defense in AWS.