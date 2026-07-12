# Cheat Sheet & Interview Guide

> A practical reference for the most commonly used Amazon Route 53 CLI commands, DNS workflows, troubleshooting techniques, and interview preparation. This chapter serves as a day-to-day operational guide for Backend Engineers, DevOps Engineers, Cloud Engineers, Platform Engineers, and AWS Solutions Architects.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Quickly recall frequently used Route 53 CLI commands
- Manage Hosted Zones and DNS records
- Configure Routing Policies
- Manage Health Checks
- Secure domains using DNSSEC
- Troubleshoot DNS issues
- Prepare for AWS certification and backend engineering interviews

---

# Why a Cheat Sheet?

Amazon Route 53 is often configured once but referenced frequently.

Instead of memorizing every command, experienced engineers remember:

- Hosted Zone workflow
- DNS record management
- Routing Policies
- Health Checks
- Domain management
- DNS troubleshooting

This chapter provides a quick operational reference.

---

# Command Syntax

General syntax:

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

# Hosted Zone Commands

## List Hosted Zones

```bash
aws route53 list-hosted-zones
```

---

## Create Hosted Zone

```bash
aws route53 create-hosted-zone
```

---

## Get Hosted Zone Details

```bash
aws route53 get-hosted-zone
```

---

## Delete Hosted Zone

```bash
aws route53 delete-hosted-zone
```

---

# DNS Record Commands

## List DNS Records

```bash
aws route53 list-resource-record-sets
```

---

## Create or Update Record

```bash
aws route53 change-resource-record-sets
```

---

## Check DNS Change Status

```bash
aws route53 get-change
```

---

# Health Check Commands

## Create Health Check

```bash
aws route53 create-health-check
```

---

## List Health Checks

```bash
aws route53 list-health-checks
```

---

## Get Health Check

```bash
aws route53 get-health-check
```

---

## Delete Health Check

```bash
aws route53 delete-health-check
```

---

# DNSSEC Commands

## View DNSSEC Status

```bash
aws route53 get-dnssec
```

---

## Create Key Signing Key

```bash
aws route53 create-key-signing-key
```

---

## Enable DNSSEC

```bash
aws route53 enable-hosted-zone-dnssec
```

---

## Disable DNSSEC

```bash
aws route53 disable-hosted-zone-dnssec
```

---

# Route 53 Domains Commands

## Check Domain Availability

```bash
aws route53domains check-domain-availability
```

---

## List Registered Domains

```bash
aws route53domains list-domains
```

---

## Get Domain Details

```bash
aws route53domains get-domain-detail
```

---

## List Domain Operations

```bash
aws route53domains list-operations
```

---

# Useful Global Options

| Option | Purpose |
|----------|----------|
| `--profile` | Use named AWS profile |
| `--output json` | JSON output |
| `--output table` | Table output |
| `--query` | Filter CLI output |
| `--debug` | Debug requests |
| `--no-cli-pager` | Disable CLI pager |

---

# Common DNS Record Types

| Record | Purpose |
|----------|----------|
| A | IPv4 Address |
| AAAA | IPv6 Address |
| CNAME | Canonical Name |
| Alias | AWS Resource |
| MX | Mail Server |
| TXT | Verification |
| NS | Name Servers |
| SOA | Zone Authority |

---

# Routing Policy Quick Reference

| Routing Policy | Best Use Case |
|----------------|---------------|
| Simple | Single application |
| Weighted | Canary deployment |
| Latency | Multi-region applications |
| Failover | Disaster Recovery |
| Geolocation | Country-specific routing |
| Geoproximity | Regional traffic optimization |
| Multi-Value | DNS load balancing |

---

# Common Errors

| Error | Cause | Resolution |
|--------|-------|------------|
| NoSuchHostedZone | Invalid Hosted Zone ID | Verify Hosted Zone |
| InvalidChangeBatch | Invalid record configuration | Validate JSON and record values |
| ConflictingDomainExists | Overlapping Hosted Zones | Review Hosted Zone hierarchy |
| Health Check Failure | Endpoint unavailable | Verify endpoint and firewall |
| DNSSEC Validation Failure | Incorrect DS record | Verify DNSSEC configuration |

---

# DNS Deployment Checklist

Before deploying DNS changes:

- □ Hosted Zone exists
- □ Correct record type
- □ Correct record value
- □ Appropriate TTL
- □ Routing Policy configured
- □ Health Check associated (if required)
- □ Alias target verified
- □ DNSSEC configured (production)
- □ Auto-renew enabled

---

# Production DNS Checklist

Every production environment should have:

- Public Hosted Zone
- Private Hosted Zone (if needed)
- Alias Records
- Health Checks
- Failover Routing
- DNSSEC
- Auto-renew enabled
- CloudWatch monitoring

---

# Disaster Recovery Checklist

Production DNS should support:

```text
Primary Region

↓

Health Check

↓

Failure

↓

Secondary Region
```

Verify:

- Health Checks
- Failover Routing
- Backup Region
- DNS propagation
- Recovery testing

---

# DNS Troubleshooting Workflow

```text
DNS Failure

↓

Hosted Zone

↓

DNS Record

↓

Routing Policy

↓

Health Check

↓

DNS Resolver

↓

Application
```

---

# Route 53 Architecture

```text
Users
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
Routing Policy
      │
      ▼
AWS Resources
```

---

# Interview Questions

## 1. What is Amazon Route 53?

**Answer**

Amazon Route 53 is AWS's highly available and scalable managed DNS service that provides domain registration, DNS hosting, health checks, traffic routing, and failover capabilities.

---

## 2. What is the difference between a Public and a Private Hosted Zone?

**Answer**

A Public Hosted Zone resolves DNS queries from the public Internet, whereas a Private Hosted Zone is associated with one or more VPCs and is only accessible from resources within those VPCs.

---

## 3. What is the difference between an Alias Record and a CNAME Record?

**Answer**

A CNAME record maps one hostname to another hostname and cannot be used for the root domain. An Alias Record is an AWS-specific Route 53 feature that points directly to supported AWS resources such as Load Balancers, CloudFront distributions, API Gateway, or S3 websites, and it can be used at the root domain.

---

## 4. What is a Health Check?

**Answer**

A Health Check continuously monitors an endpoint using HTTP, HTTPS, TCP, or CloudWatch Alarms. Route 53 uses the health status to determine whether traffic should continue to be routed to that endpoint.

---

## 5. What is DNS Failover?

**Answer**

DNS Failover automatically redirects traffic from an unhealthy primary endpoint to a healthy secondary endpoint using Health Checks and Failover Routing Policies.

---

## 6. What is DNSSEC?

**Answer**

DNSSEC digitally signs DNS records, allowing DNS resolvers to verify the authenticity and integrity of DNS responses. It protects against DNS spoofing and cache poisoning attacks.

---

## 7. What is the purpose of TTL?

**Answer**

TTL (Time To Live) specifies how long DNS resolvers cache a DNS record before requesting it again. Lower TTL values allow faster propagation of changes, while higher values reduce DNS query traffic.

---

## 8. What Routing Policy would you use for a canary deployment?

**Answer**

Weighted Routing allows traffic to be split between application versions based on configured weights, making it ideal for canary deployments and gradual rollouts.

---

## 9. How would you route users to the nearest AWS Region?

**Answer**

Latency-Based Routing directs users to the AWS Region with the lowest network latency, improving application performance for globally distributed users.

---

## 10. How would you troubleshoot DNS resolution issues?

**Answer**

I would verify the Hosted Zone, inspect DNS records, confirm the registrar's Name Server configuration, check the status of recent DNS changes, review Routing Policies and Health Checks, validate DNSSEC if enabled, and use tools such as `dig`, `nslookup`, or `host` to inspect DNS responses.

---

# Senior Engineer Tips

Experienced cloud engineers typically:

- Use Alias Records instead of static IP addresses.
- Separate production and non-production Hosted Zones.
- Enable DNSSEC for public domains.
- Configure Health Checks for critical services.
- Use Failover Routing for disaster recovery.
- Keep TTL values low during migrations.
- Enable automatic domain renewal.
- Manage DNS using Infrastructure as Code.
- Audit DNS records regularly.
- Monitor domain expiration dates.

---

# Quick Reference

| Task | Command |
|------|---------|
| List Hosted Zones | `aws route53 list-hosted-zones` |
| Create Hosted Zone | `aws route53 create-hosted-zone` |
| List DNS Records | `aws route53 list-resource-record-sets` |
| Update DNS Record | `aws route53 change-resource-record-sets` |
| Create Health Check | `aws route53 create-health-check` |
| List Health Checks | `aws route53 list-health-checks` |
| Check Domain Availability | `aws route53domains check-domain-availability` |
| List Registered Domains | `aws route53domains list-domains` |
| View DNSSEC Status | `aws route53 get-dnssec` |
| Check DNS Change Status | `aws route53 get-change` |

---

# Final Thoughts

Amazon Route 53 is much more than a DNS service. It provides intelligent traffic routing, health monitoring, disaster recovery, domain management, and secure DNS resolution. Mastering Route 53 and its CLI enables you to build highly available, globally distributed, and production-ready cloud applications.

---
