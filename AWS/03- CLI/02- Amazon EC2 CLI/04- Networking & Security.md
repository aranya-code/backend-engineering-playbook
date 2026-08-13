# Networking & Security

> Learn how to configure networking and secure Amazon EC2 instances using the AWS CLI. This chapter covers Security Groups, Key Pairs, Elastic IPs, Elastic Network Interfaces (ENIs), VPC networking, and production security best practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand EC2 networking components.
- Create and manage Security Groups.
- Configure inbound and outbound rules.
- Work with Key Pairs.
- Allocate and associate Elastic IPs.
- Manage Elastic Network Interfaces (ENIs).
- Understand public vs private instances.
- Troubleshoot connectivity issues.
- Apply production-ready security practices.

---

# EC2 Networking Architecture

Every EC2 instance exists inside a Virtual Private Cloud (VPC).

```text
AWS Account
      │
      ▼
VPC
      │
      ▼
Subnet
      │
      ▼
Network Interface (ENI)
      │
      ▼
Security Group
      │
      ▼
EC2 Instance
```

Every network request flows through these networking components.

---

# Understanding Security Groups

A Security Group acts as a virtual firewall.

It controls:

- Incoming traffic (Inbound Rules)
- Outgoing traffic (Outbound Rules)

Security Groups are:

- Stateful
- Attached to ENIs
- Allow rules only
- Deny by default

---

# Listing Security Groups

```bash
aws ec2 describe-security-groups
```

Returns:

- Security Group ID
- Group Name
- Description
- VPC
- Rules

---

# View a Specific Security Group

```bash
aws ec2 describe-security-groups \
--group-ids sg-0123456789abcdef0
```

---

# Create a Security Group

```bash
aws ec2 create-security-group \
--group-name backend-sg \
--description "Backend Application Security Group" \
--vpc-id vpc-0123456789abcdef0
```

Example response:

```json
{
    "GroupId":"sg-0123456789abcdef0"
}
```

---

# Allow SSH Access

```bash
aws ec2 authorize-security-group-ingress \
--group-id sg-0123456789abcdef0 \
--protocol tcp \
--port 22 \
--cidr 203.0.113.10/32
```

Always restrict SSH to trusted IP addresses.

Avoid:

```text
0.0.0.0/0
```

unless absolutely necessary.

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
aws ec2 revoke-security-group-ingress \
--group-id sg-0123456789abcdef0 \
--protocol tcp \
--port 22 \
--cidr 203.0.113.10/32
```

---

# Security Group Workflow

```text
Client Request
       │
       ▼
Security Group
       │
       ▼
Allowed?
       │
  Yes / No
       │
       ▼
EC2 Instance
```

If traffic is not explicitly allowed, it is blocked.

---

# Understanding Key Pairs

Key Pairs provide secure SSH authentication.

A Key Pair consists of:

- Public Key (stored in AWS)
- Private Key (stored securely by you)

AWS never stores the private key.

---

# List Key Pairs

```bash
aws ec2 describe-key-pairs
```

---

# Create a Key Pair

```bash
aws ec2 create-key-pair \
--key-name backend-key
```

Store the private key securely.

Do **not** commit it to Git repositories.

---

# Delete a Key Pair

```bash
aws ec2 delete-key-pair \
--key-name backend-key
```

Deleting a Key Pair does not remove the public key from existing instances.

---

# Elastic IP Addresses

An Elastic IP (EIP) is a static public IPv4 address.

Unlike the default public IP:

- It remains allocated to your AWS account.
- It can be reassigned to another instance.

Useful for:

- Production servers
- Bastion hosts
- Static DNS records

---

# Allocate an Elastic IP

```bash
aws ec2 allocate-address
```

Example response:

```json
{
    "PublicIp":"203.0.113.25",
    "AllocationId":"eipalloc-0123456789abcdef0"
}
```

---

# Associate an Elastic IP

```bash
aws ec2 associate-address \
--instance-id i-0123456789abcdef0 \
--allocation-id eipalloc-0123456789abcdef0
```

---

# Release an Elastic IP

```bash
aws ec2 release-address \
--allocation-id eipalloc-0123456789abcdef0
```

Release unused Elastic IPs to avoid unnecessary charges.

---

# Elastic Network Interfaces (ENIs)

Every EC2 instance has at least one Elastic Network Interface.

An ENI contains:

- Private IP
- MAC Address
- Security Groups
- Network configuration

---

# List ENIs

```bash
aws ec2 describe-network-interfaces
```

---

# Attach an ENI

```bash
aws ec2 attach-network-interface \
--network-interface-id eni-0123456789abcdef0 \
--instance-id i-0123456789abcdef0 \
--device-index 1
```

---

# Public vs Private Instances

Public Instance

- Public IP
- Internet Gateway
- Direct internet access

Private Instance

- Private IP only
- No direct internet access
- Accessed through:

  - Bastion Host
  - VPN
  - AWS Systems Manager Session Manager

Production workloads are commonly deployed in private subnets.

---

# Bastion Hosts

A Bastion Host is a hardened EC2 instance used for administrative access.

Typical architecture:

```text
Internet
      │
      ▼
Bastion Host
      │
      ▼
Private EC2 Instances
```

Only the Bastion Host requires inbound SSH access.

---

# Connectivity Troubleshooting

Unable to connect?

Check:

- Instance state
- Security Group
- Network ACL
- Route Table
- Internet Gateway
- Public IP
- SSH Key
- Local firewall

---

# Viewing Network Information

Retrieve public IP:

```bash
aws ec2 describe-instances \
--query "Reservations[].Instances[].PublicIpAddress"
```

Retrieve private IP:

```bash
aws ec2 describe-instances \
--query "Reservations[].Instances[].PrivateIpAddress"
```

---

# Production Best Practices

- Restrict SSH access.
- Prefer Session Manager over SSH.
- Use private subnets whenever possible.
- Enable Security Group least privilege.
- Use Elastic IPs only when necessary.
- Tag networking resources.
- Regularly review Security Group rules.
- Remove unused Elastic IPs.

---

# Real-World Workflow

Deploying a production EC2 instance.

```text
Create Security Group
        │
        ▼
Launch EC2 Instance
        │
        ▼
Assign IAM Role
        │
        ▼
Associate Elastic IP (if required)
        │
        ▼
Verify Connectivity
        │
        ▼
Deploy Application
```

---

# Common Errors

## Connection Timed Out

Possible causes:

- Port not open
- Security Group blocks traffic
- Route table issue
- No Internet Gateway
- Incorrect public IP

---

## Permission Denied (SSH)

Possible causes:

- Wrong private key
- Incorrect file permissions
- Wrong EC2 username

---

## InvalidGroup.NotFound

Verify Security Group ID:

```bash
aws ec2 describe-security-groups
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
VPC
      │
      ▼
Subnet
      │
      ▼
Security Group
      │
      ▼
Elastic Network Interface
      │
      ▼
EC2 Instance
```

Every inbound and outbound packet follows this networking path.

---

# Interview Note

### Question

**What is the difference between a Security Group and a Network ACL?**

### Answer

A **Security Group** is a stateful virtual firewall attached to an EC2 instance's network interface. It only contains allow rules, and return traffic is automatically permitted. A **Network ACL (NACL)** is a stateless firewall applied at the subnet level. It supports both allow and deny rules, and return traffic must be explicitly permitted. In practice, Security Groups protect individual instances, while NACLs provide an additional layer of subnet-level security.

---

# Key Takeaways

- Every EC2 instance is launched inside a VPC and subnet.
- Security Groups are stateful firewalls attached to network interfaces.
- Key Pairs provide secure SSH authentication.
- Elastic IPs offer static public IP addresses.
- Elastic Network Interfaces contain an instance's networking configuration.
- Prefer private subnets and Session Manager for production workloads.
- Apply the Principle of Least Privilege to all network access.
- Regularly review Security Group rules and networking resources.

---

