# Hosted Zones & DNS Records

> Learn how to create, manage, and maintain Amazon Route 53 Hosted Zones and DNS records using the AWS CLI. This chapter covers Public and Private Hosted Zones, common DNS record types, Alias Records, record management, TTL, DNS propagation, and production DNS best practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand Hosted Zones
- Create Public and Private Hosted Zones
- Manage DNS records
- Understand common DNS record types
- Configure Alias Records
- Understand TTL and DNS propagation
- Build production DNS architectures

---

# What is a Hosted Zone?

A Hosted Zone is a container for DNS records.

```text
example.com

↓

Hosted Zone

↓

DNS Records
```

Every domain managed by Route 53 requires a Hosted Zone.

---

# Types of Hosted Zones

Amazon Route 53 supports two types.

```text
Hosted Zones

│

├── Public Hosted Zone

└── Private Hosted Zone
```

---

# Public Hosted Zone

Public Hosted Zones are accessible from anywhere on the Internet.

Example:

```text
www.example.com

↓

Public Hosted Zone

↓

Internet
```

Typical use cases:

- Websites
- APIs
- Public Load Balancers
- Public Applications

---

# Private Hosted Zone

Private Hosted Zones are only accessible from associated VPCs.

Example:

```text
VPC

↓

Private Hosted Zone

↓

database.internal
```

Typical use cases:

- Internal applications
- Private APIs
- Internal databases
- Service discovery

---

# Hosted Zone Architecture

```text
Domain

↓

Hosted Zone

↓

DNS Records

↓

AWS Resources
```

---

# Create a Public Hosted Zone

```bash
aws route53 create-hosted-zone \
--name example.com \
--caller-reference "$(date +%s)"
```

The `caller-reference` must be unique for every request.

---

# Create a Private Hosted Zone

```bash
aws route53 create-hosted-zone \
--name internal.example.com \
--caller-reference "$(date +%s)" \
--hosted-zone-config Comment="Private Zone",PrivateZone=true \
--vpc VPCRegion=ap-south-1,VPCId=vpc-0123456789abcdef0
```

Private Hosted Zones require an associated VPC.

---

# List Hosted Zones

```bash
aws route53 list-hosted-zones
```

Displays:

- Hosted Zone ID
- Domain
- Private/Public
- Record count

---

# Get Hosted Zone Details

```bash
aws route53 get-hosted-zone \
--id Z123456789ABC
```

Returns:

- Name Servers
- Zone configuration
- Associated VPCs

---

# Delete a Hosted Zone

```bash
aws route53 delete-hosted-zone \
--id Z123456789ABC
```

A Hosted Zone cannot be deleted until all custom DNS records are removed.

---

# What are DNS Records?

DNS records tell Route 53 how to respond to DNS queries.

Example:

```text
www.example.com

↓

54.220.18.25
```

---

# Common DNS Record Types

| Record | Purpose |
|---------|----------|
| A | IPv4 Address |
| AAAA | IPv6 Address |
| CNAME | Canonical Name |
| MX | Mail Exchange |
| TXT | Verification & Security |
| NS | Name Servers |
| SOA | Start of Authority |
| Alias | AWS Resource Mapping |

---

# A Record

Maps a hostname to an IPv4 address.

Example:

```text
www.example.com

↓

54.220.18.25
```

---

# AAAA Record

Maps a hostname to an IPv6 address.

Example:

```text
www.example.com

↓

2406:da00::15
```

---

# CNAME Record

Maps one hostname to another.

Example:

```text
blog.example.com

↓

hosting-provider.example.net
```

Cannot be used for the root domain.

---

# Alias Record

Alias records are unique to Route 53.

Instead of:

```text
www.example.com

↓

54.220.18.25
```

You can point directly to:

- Application Load Balancer
- Network Load Balancer
- CloudFront
- S3 Website
- API Gateway
- Global Accelerator

---

# Alias Record Benefits

Advantages:

- No hardcoded IPs
- Automatically follows AWS resource changes
- No additional DNS lookup
- Supports root domains

---

# MX Record

Specifies mail servers.

Example:

```text
example.com

↓

mail.example.com
```

---

# TXT Record

Common uses:

- Domain verification
- SPF
- DKIM
- DMARC
- Google verification
- Microsoft verification

---

# NS Record

Contains the authoritative name servers.

Example:

```text
ns-123.awsdns.com
```

Normally managed automatically.

---

# SOA Record

Contains metadata for the Hosted Zone.

Includes:

- Primary Name Server
- Email
- Refresh interval
- Retry interval
- Expiration

Automatically created by Route 53.

---

# List DNS Records

```bash
aws route53 list-resource-record-sets \
--hosted-zone-id Z123456789ABC
```

Displays all records.

---

# Change Batch

DNS changes are submitted using a **Change Batch**.

Example:

```text
Change Batch JSON

↓

Route 53

↓

DNS Updated
```

---

# Create an A Record

Example `change-batch.json`

```json
{
  "Comment": "Create A Record",
  "Changes": [
    {
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "www.example.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [
          {
            "Value": "54.220.18.25"
          }
        ]
      }
    }
  ]
}
```

Apply:

```bash
aws route53 change-resource-record-sets \
--hosted-zone-id Z123456789ABC \
--change-batch file://change-batch.json
```

---

# Update a Record

Replace:

```text
Action

↓

UPSERT
```

UPSERT creates the record if it doesn't exist or updates it if it already exists.

---

# Delete a Record

Replace:

```text
Action

↓

DELETE
```

The record definition must exactly match the existing record.

---

# TTL (Time To Live)

TTL determines how long DNS resolvers cache a record.

Example:

```text
TTL

300 Seconds
```

After 300 seconds, the resolver requests the record again.

---

# TTL Best Practices

Typical values:

| TTL | Use Case |
|------|----------|
| 60 | Frequent changes |
| 300 | Most applications |
| 900 | Stable services |
| 3600 | Rarely changing records |

Lower TTL enables faster updates but increases DNS queries.

---

# DNS Propagation

When a record changes:

```text
Update Record

↓

DNS Servers

↓

Resolvers Refresh Cache

↓

Users See Change
```

TTL influences how quickly clients observe updates.

---

# Verify DNS Changes

Check change status:

```bash
aws route53 get-change \
--id C123456789ABCDEF
```

Status values:

- `PENDING`
- `INSYNC`

`INSYNC` indicates Route 53 has propagated the change to its authoritative DNS servers.

---

# Common Errors

## NoSuchHostedZone

Verify:

- Hosted Zone ID
- AWS Account

---

## InvalidChangeBatch

Possible causes:

- Duplicate record
- Invalid JSON
- Invalid record type
- Missing fields

---

## ConflictingDomainExists

Occurs when attempting to create overlapping Hosted Zones.

Review domain hierarchy.

---

# Production Best Practices

- Use Public Hosted Zones only for internet-facing applications.
- Use Private Hosted Zones for internal services.
- Prefer Alias Records for AWS resources.
- Use meaningful TTL values.
- Version DNS changes through Infrastructure as Code.
- Remove unused records regularly.
- Keep Hosted Zones organized.
- Validate changes before production deployments.

---

# Real-World Workflow

```text
Register Domain

↓

Create Hosted Zone

↓

Create DNS Records

↓

Point to Load Balancer

↓

Verify DNS

↓

Production
```

---

# Architecture Note

```text
Internet User
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
Application Load Balancer
       │
       ▼
Application
```

Route 53 acts as the authoritative DNS service while routing client requests to the appropriate AWS resources.

---

# Interview Note

### Question

**What is the difference between an Alias Record and a CNAME Record?**

### Answer

A **CNAME Record** maps one domain name to another domain name and cannot be used for the root domain (zone apex). An **Alias Record** is an AWS-specific Route 53 feature that maps a domain directly to supported AWS resources such as Application Load Balancers, CloudFront distributions, S3 static websites, and API Gateway. Alias records support the root domain, automatically track changes to AWS resource IP addresses, and do not incur additional DNS lookup charges.

---

# Key Takeaways

- Hosted Zones store DNS records for a domain.
- Route 53 supports Public and Private Hosted Zones.
- DNS records determine how domain names are resolved.
- Alias Records are preferred for AWS resources.
- DNS changes are managed using Change Batches.
- TTL controls DNS caching behavior.
- Proper Hosted Zone and DNS record management is essential for reliable production applications.