# Introduction to Route 53 CLI

> Learn how to manage domains, DNS records, hosted zones, health checks, and traffic routing using Amazon Route 53 and the AWS Command Line Interface (AWS CLI). This chapter introduces DNS fundamentals, Route 53 architecture, hosted zones, and the most commonly used Route 53 CLI commands.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand DNS fundamentals
- Understand Amazon Route 53
- Navigate Route 53 CLI commands
- Understand Hosted Zones
- Understand DNS records
- Understand DNS resolution
- Build a foundation for AWS networking

---

# Why Learn Route 53?

Every application on the Internet depends on DNS.

Instead of users remembering:

```text
3.111.45.201
```

They access:

```text
www.example.com
```

DNS translates human-readable domain names into IP addresses.

Amazon Route 53 is AWS's managed DNS service that provides:

- Domain registration
- DNS hosting
- Health checks
- Traffic routing
- High availability
- Failover
- Latency optimization

It is one of the core networking services in AWS.

---

# What is DNS?

DNS stands for:

> **Domain Name System**

DNS acts like the Internet's phonebook.

Instead of remembering IP addresses, users access resources using domain names.

Example:

```text
google.com

↓

DNS Lookup

↓

142.x.x.x
```

---

# What is Amazon Route 53?

Amazon Route 53 is AWS's highly available and scalable DNS service.

It provides:

- Domain registration
- DNS resolution
- Hosted Zones
- Health Checks
- Traffic Routing
- DNS Failover

Route 53 is globally distributed and designed for high availability.

---

# Why is it Called Route 53?

The name comes from:

```text
Port 53
```

The standard TCP/UDP port used by DNS.

---

# How DNS Resolution Works

```text
User

↓

Browser

↓

DNS Resolver

↓

Route 53

↓

IP Address

↓

Application
```

The browser then connects to the returned IP address.

---

# Route 53 Architecture

```text
Domain

↓

Hosted Zone

↓

DNS Records

↓

AWS Resources
```

A Hosted Zone stores DNS records for a domain.

---

# Common Route 53 Use Cases

Examples include:

- Website hosting
- API routing
- Load Balancer DNS
- Multi-region applications
- Disaster recovery
- Health-based routing
- Domain registration
- Internal DNS

---

# Common DNS Record Types

Frequently used records include:

| Record | Purpose |
|---------|----------|
| A | IPv4 Address |
| AAAA | IPv6 Address |
| CNAME | Alias to another hostname |
| MX | Mail server |
| TXT | Verification and SPF/DKIM |
| NS | Name servers |
| SOA | Zone authority |
| Alias | AWS resource mapping |

---

# Public vs Private Hosted Zones

Public Hosted Zone

```text
Internet

↓

Route 53

↓

example.com
```

Accessible from anywhere.

---

Private Hosted Zone

```text
VPC

↓

Route 53

↓

internal.company.local
```

Accessible only inside associated VPCs.

---

# Route 53 Routing

Route 53 supports advanced routing strategies.

Examples:

- Simple
- Weighted
- Latency
- Failover
- Geolocation
- Geoproximity
- Multi-Value Answer

These topics are covered later in this guide.

---

# Route 53 Integrations

Route 53 integrates with:

- Elastic Load Balancer
- CloudFront
- API Gateway
- S3 Static Websites
- EC2
- Global Accelerator
- VPC
- Health Checks

---

# Route 53 CLI Namespace

Unlike VPC, Route 53 has its own namespace.

```bash
aws route53 <operation>
```

Examples:

```bash
aws route53 list-hosted-zones
```

```bash
aws route53 create-hosted-zone
```

```bash
aws route53 list-resource-record-sets
```

---

# List Hosted Zones

```bash
aws route53 list-hosted-zones
```

Displays:

- Hosted Zone ID
- Domain Name
- Private/Public
- Record Count

---

# Get Hosted Zone Details

```bash
aws route53 get-hosted-zone \
--id Z123456789ABC
```

Returns:

- Hosted Zone details
- Name Servers
- VPC associations
- Configuration

---

# List DNS Records

```bash
aws route53 list-resource-record-sets \
--hosted-zone-id Z123456789ABC
```

Displays every DNS record in the Hosted Zone.

---

# Verify AWS Identity

Before modifying production DNS:

```bash
aws sts get-caller-identity
```

Always verify the correct AWS account.

---

# Global CLI Options

Examples:

```bash
aws route53 list-hosted-zones \
--profile production
```

```bash
aws route53 list-hosted-zones \
--output table
```

---

# Production Tip

Separate environments.

Example:

```text
production.example.com

staging.example.com

dev.example.com
```

Avoid mixing production and development DNS records.

---

# Architecture Note

```text
User
      │
      ▼
DNS Resolver
      │
      ▼
Amazon Route 53
      │
      ▼
Hosted Zone
      │
      ▼
DNS Records
      │
      ▼
AWS Resources
```

Route 53 acts as the authoritative DNS service for your domain.

---

# Interview Note

### Question

**What is Amazon Route 53?**

### Answer

Amazon Route 53 is AWS's highly available and scalable Domain Name System (DNS) service. It provides domain registration, DNS hosting, health checks, traffic routing, and failover capabilities. Route 53 translates domain names into IP addresses or AWS resource endpoints, enabling users to access applications using human-readable names instead of IP addresses.

---

# Key Takeaways

- DNS translates domain names into IP addresses.
- Amazon Route 53 is AWS's managed DNS service.
- Hosted Zones store DNS records for domains.
- Route 53 supports both public and private DNS.
- Route 53 integrates with many AWS services.
- Most Route 53 operations use the `aws route53` CLI namespace.
- Understanding DNS is essential for designing highly available cloud applications.