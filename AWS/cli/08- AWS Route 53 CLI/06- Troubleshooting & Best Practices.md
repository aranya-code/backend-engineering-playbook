# Troubleshooting & Best Practices

> Learn how to troubleshoot Amazon Route 53 issues and apply production-ready DNS best practices. This chapter covers DNS resolution failures, Hosted Zone issues, routing policies, Health Checks, DNSSEC, domain registration, propagation delays, and operational recommendations for highly available production environments.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Troubleshoot Route 53 issues
- Debug DNS resolution problems
- Diagnose Hosted Zone configuration issues
- Troubleshoot routing policies
- Verify Health Checks
- Troubleshoot DNSSEC
- Apply production DNS best practices

---

# DNS Troubleshooting Workflow

Whenever DNS fails:

```text
Client

↓

DNS Resolver

↓

Route 53

↓

Hosted Zone

↓

DNS Record

↓

Application
```

Check each layer individually.

---

# Verify Hosted Zones

List all Hosted Zones.

```bash
aws route53 list-hosted-zones
```

Verify:

- Correct domain
- Public or Private Hosted Zone
- Hosted Zone ID

---

# Inspect Hosted Zone

```bash
aws route53 get-hosted-zone \
--id Z123456789ABC
```

Check:

- Name Servers
- VPC associations
- Configuration
- Hosted Zone type

---

# Verify DNS Records

```bash
aws route53 list-resource-record-sets \
--hosted-zone-id Z123456789ABC
```

Verify:

- Record Name
- Record Type
- TTL
- Alias target
- IP address

---

# DNS Record Not Resolving

Possible causes:

- Incorrect record
- Wrong Hosted Zone
- DNS propagation
- TTL caching
- Incorrect Name Servers

Workflow:

```text
Domain

↓

Hosted Zone

↓

Record Exists?

↓

TTL

↓

Propagation

↓

Resolver Cache
```

---

# Hosted Zone Not Found

Common error:

```text
NoSuchHostedZone
```

Verify:

- Hosted Zone ID
- AWS Account
- Region-independent Route 53 configuration

---

# Incorrect Name Servers

Verify the registrar uses the Route 53 Name Servers.

Example:

```text
Registrar

↓

ns-123.awsdns.com

ns-456.awsdns.net

ns-789.awsdns.org

ns-321.awsdns.co.uk
```

If the registrar points elsewhere, Route 53 records will not be used.

---

# DNS Propagation

DNS changes are not always immediate.

Workflow:

```text
Update Record

↓

Route 53

↓

DNS Resolver Cache

↓

Users
```

TTL determines how long resolvers cache records.

---

# Verify Change Status

```bash
aws route53 get-change \
--id C123456789ABCDEF
```

Possible results:

```text
PENDING
```

```text
INSYNC
```

`INSYNC` means Route 53 has propagated the change to its authoritative name servers.

---

# Alias Record Issues

Verify:

- Target resource exists
- Correct Hosted Zone ID
- Alias target supports Route 53
- Resource is healthy

Common resources:

- ALB
- NLB
- CloudFront
- S3 Website
- API Gateway

---

# Health Check Issues

List Health Checks.

```bash
aws route53 list-health-checks
```

Verify:

- Endpoint
- Port
- Protocol
- Resource Path
- Failure Threshold

---

# Endpoint Always Unhealthy

Possible causes:

- Incorrect IP
- Wrong URL
- Firewall blocking requests
- SSL certificate errors
- Application failure

Verify:

```text
/health

↓

HTTP 200
```

---

# Routing Policy Issues

Check:

- Routing Policy
- Health Check association
- Record names
- Record types
- Weights
- Regions

Incorrect routing configuration often results in unexpected DNS responses.

---

# Weighted Routing Problems

Verify:

```text
Weight

↓

Correct Percentage
```

Example:

```text
80

20
```

Traffic distribution is proportional to configured weights.

---

# Failover Routing Problems

Verify:

```text
Primary

↓

Health Check

↓

Healthy?
```

If the Health Check never becomes healthy, failover may occur continuously.

---

# Latency Routing Problems

Verify:

- AWS Region configuration
- Endpoint health
- Record association

Latency Routing is based on AWS latency measurements, not geographic distance.

---

# Private Hosted Zone Issues

Verify:

- Correct VPC association
- DNS Hostnames enabled
- DNS Resolution enabled

Without VPC association, private records cannot be resolved.

---

# DNSSEC Issues

Verify:

- DNSSEC enabled
- KSK configured
- Registrar DS record
- DNSSEC validation status

Improper DNSSEC configuration may prevent successful DNS resolution.

---

# Domain Registration Problems

Check:

```bash
aws route53domains get-domain-detail \
--domain-name example.com
```

Verify:

- Domain status
- Auto renewal
- Contact information
- Name Servers

---

# Common Errors

## NoSuchHostedZone

Hosted Zone ID is incorrect.

Verify the Hosted Zone exists.

---

## InvalidChangeBatch

Possible causes:

- Invalid JSON
- Duplicate records
- Invalid record type
- Incorrect Alias configuration

---

## ConflictingDomainExists

Occurs when overlapping Hosted Zones exist.

Review Hosted Zone hierarchy.

---

## Health Check Failure

Possible causes:

- Wrong endpoint
- Firewall rules
- Application unavailable
- Incorrect resource path

---

## DNSSEC Validation Failure

Possible causes:

- Incorrect DS record
- Registrar mismatch
- Invalid signing configuration

---

# DNS Debugging Tools

Useful commands:

```bash
nslookup example.com
```

```bash
dig example.com
```

```bash
host example.com
```

These tools verify:

- IP address
- Name Servers
- TTL
- Authority

---

# Production Best Practices

## Use Alias Records

Prefer:

```text
Route 53

↓

Alias

↓

Application Load Balancer
```

Instead of static IP addresses.

---

## Keep TTL Appropriate

Recommended:

| Scenario | TTL |
|-----------|----:|
| Frequent deployments | 60 |
| Standard applications | 300 |
| Stable production | 900–3600 |

---

## Separate Environments

Example:

```text
dev.example.com

staging.example.com

api.example.com

www.example.com
```

Avoid mixing environments.

---

## Enable Health Checks

Every production endpoint should have:

```text
Application

↓

Health Check
```

---

## Enable DNSSEC

Protect production domains against:

- DNS spoofing
- Cache poisoning
- DNS tampering

---

## Use Least Privilege

IAM policies should restrict:

- Hosted Zone modification
- Domain registration
- DNSSEC configuration

---

## Enable Auto Renewal

Never allow production domains to expire.

Always enable:

```text
Auto Renewal

↓

Enabled
```

---

## Monitor DNS

Monitor:

- Health Checks
- CloudWatch Alarms
- Domain expiration
- DNSSEC status

---

# Real-World Workflow

```text
Register Domain

↓

Create Hosted Zone

↓

Create DNS Records

↓

Configure Routing Policy

↓

Configure Health Checks

↓

Enable DNSSEC

↓

Production
```

---

# Architecture Note

```text
Internet User
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
Healthy AWS Resource
```

A production DNS architecture combines Hosted Zones, Routing Policies, Health Checks, and DNSSEC to provide highly available, secure, and resilient name resolution.

---

# Interview Note

### Question

**How would you troubleshoot a website that cannot be reached even though the EC2 instance is running?**

### Answer

I would first verify that the domain points to the correct Hosted Zone and inspect the DNS records using `list-resource-record-sets`. Next, I would confirm that the domain registrar is configured with the correct Route 53 Name Servers. I would check the DNS change status, verify that the Alias or A record points to the correct resource, review any Routing Policies and Health Checks, and ensure DNS propagation has completed. If DNS is correct, I would then investigate the underlying infrastructure such as the Load Balancer, Security Groups, Route Tables, and the application itself.

---

# Key Takeaways

- Always troubleshoot DNS from the resolver to the application.
- Verify Hosted Zones and DNS records before investigating infrastructure.
- Route 53 Health Checks improve availability and enable automatic failover.
- Alias Records are preferred for AWS resources.
- DNSSEC protects against DNS spoofing and tampering.
- Appropriate TTL values balance update speed and DNS query volume.
- Well-designed DNS architecture is a critical component of highly available cloud applications.