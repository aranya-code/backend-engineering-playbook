# Domain Registration & DNSSEC

> Learn how to register and manage domains using Amazon Route 53, configure domain settings, understand WHOIS, domain transfers, DNSSEC, and secure DNS infrastructure using the AWS CLI. This chapter also covers production domain management and security best practices.

---

# Learning Objectives

After completing this chapter, you will be able to:

- Understand domain registration
- Register and manage domains
- Understand domain lifecycle
- Configure domain contacts
- Understand WHOIS
- Understand DNSSEC
- Secure Route 53 Hosted Zones
- Apply production domain management practices

---

# What is a Domain Name?

A domain name is the human-readable address used to identify resources on the Internet.

Example:

```text
example.com
```

Instead of:

```text
54.210.45.32
```

DNS translates the domain name into an IP address.

---

# Domain Hierarchy

Example:

```text
www.example.com
```

Breakdown:

```text
www

↓

Subdomain

────────────

example

↓

Second-Level Domain

────────────

.com

↓

Top-Level Domain (TLD)
```

---

# Top-Level Domains (TLDs)

Common TLDs include:

```text
.com

.net

.org

.io

.dev

.ai

.in

.co

.edu

.gov
```

Each TLD is managed by a registry.

---

# Domain Registration

Route 53 can act as a domain registrar.

Typical workflow:

```text
Search Domain

↓

Purchase Domain

↓

Configure DNS

↓

Deploy Website
```

---

# Register a Domain

Domain registration is currently supported through:

- AWS Console
- Route 53 Domains API

CLI support is available through the Route 53 Domains service.

Example:

```bash
aws route53domains check-domain-availability \
--domain-name example.com
```

---

# Check Domain Availability

```bash
aws route53domains check-domain-availability \
--domain-name mycompany.com
```

Possible responses:

```text
AVAILABLE
```

or

```text
UNAVAILABLE
```

---

# List Registered Domains

```bash
aws route53domains list-domains
```

Displays:

- Domain Name
- Expiration Date
- Auto Renewal Status

---

# Get Domain Details

```bash
aws route53domains get-domain-detail \
--domain-name example.com
```

Returns:

- Registration status
- Contacts
- Name servers
- Auto-renew settings

---

# Enable Auto Renewal

Production domains should always enable:

```text
Auto Renewal

↓

Enabled
```

This helps prevent accidental domain expiration.

---

# Domain Lifecycle

```text
Available

↓

Registered

↓

Active

↓

Renewal

↓

Expiration

↓

Grace Period

↓

Redemption

↓

Released
```

Expired domains may become available for registration by others.

---

# WHOIS

WHOIS stores registration information.

Typical information:

- Owner
- Registrar
- Registration Date
- Expiration Date
- Name Servers

Many registrars support WHOIS privacy.

---

# Name Servers

Every Route 53 Hosted Zone receives four authoritative Name Servers.

Example:

```text
ns-123.awsdns.com

ns-456.awsdns.net

ns-789.awsdns.org

ns-321.awsdns.co.uk
```

Your registrar must point the domain to these Name Servers.

---

# Domain Transfer

Existing domains can be transferred to Route 53.

Typical process:

```text
Unlock Domain

↓

Obtain Authorization Code

↓

Transfer Domain

↓

Approve Transfer
```

---

# Transfer Domain Status

```bash
aws route53domains list-operations
```

Displays:

- Pending
- Successful
- Failed

---

# What is DNSSEC?

DNSSEC stands for:

> **Domain Name System Security Extensions**

It protects DNS responses from tampering.

---

# Why DNSSEC?

Without DNSSEC:

```text
User

↓

Fake DNS Response

↓

Malicious Website
```

With DNSSEC:

```text
User

↓

DNSSEC Validation

↓

Verified DNS Response
```

---

# DNSSEC Architecture

```text
User

↓

DNS Resolver

↓

DNSSEC Validation

↓

Route 53

↓

Authentic DNS Record
```

---

# DNSSEC Components

Important concepts:

```text
Hosted Zone

↓

Key Signing Key (KSK)

↓

Zone Signing Key (ZSK)

↓

Digital Signature

↓

DNS Response
```

---

# Enable DNSSEC

Hosted Zones can be configured to sign DNS records.

High-level workflow:

```text
Hosted Zone

↓

Create KSK

↓

Enable DNSSEC

↓

Update Registrar
```

---

# Create a Key Signing Key

Example:

```bash
aws route53 create-key-signing-key
```

AWS manages the signing process after DNSSEC is enabled.

---

# List Key Signing Keys

```bash
aws route53 get-dnssec
```

Returns:

- DNSSEC status
- Key Signing Keys
- Signing configuration

---

# Disable DNSSEC

If required:

```bash
aws route53 disable-hosted-zone-dnssec
```

Use with caution, especially in production environments.

---

# DNSSEC Benefits

Advantages:

- Prevents DNS spoofing
- Prevents cache poisoning
- Improves DNS integrity
- Verifies DNS authenticity

---

# Route 53 and DNSSEC

Route 53 supports:

- DNSSEC signing for Hosted Zones
- Secure DNS responses
- Automatic signature management

---

# Domain Management Workflow

```text
Register Domain

↓

Create Hosted Zone

↓

Configure Records

↓

Update Name Servers

↓

Enable DNSSEC

↓

Production
```

---

# Common Errors

## Domain Already Exists

Occurs when:

```text
example.com
```

is already registered.

Choose another domain.

---

## InvalidDomainName

Possible causes:

- Invalid characters
- Incorrect format
- Unsupported TLD

---

## Transfer Failed

Verify:

- Domain unlocked
- Authorization code
- Registrar approval

---

## DNSSEC Validation Failure

Possible causes:

- Incorrect DS record
- Registrar configuration
- Incomplete DNSSEC setup

---

# Production Best Practices

- Enable automatic domain renewal.
- Register domains with organizational accounts.
- Use WHOIS privacy where available.
- Secure registrar accounts with MFA.
- Enable DNSSEC for public domains.
- Monitor domain expiration dates.
- Keep contact information current.
- Restrict access using IAM.

---

# Real-World Workflow

```text
Purchase Domain

↓

Create Hosted Zone

↓

Configure DNS

↓

Point to Load Balancer

↓

Enable DNSSEC

↓

Deploy Application
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
DNSSEC Validation
       │
       ▼
Amazon Route 53
       │
       ▼
Hosted Zone
       │
       ▼
Application Load Balancer
       │
       ▼
Application
```

DNSSEC adds a layer of cryptographic trust, ensuring users receive authentic DNS responses rather than forged records.

---

# Interview Note

### Question

**What is DNSSEC, and why is it important?**

### Answer

DNSSEC (Domain Name System Security Extensions) is a set of security extensions that digitally signs DNS records to verify their authenticity and integrity. It protects against attacks such as DNS spoofing and cache poisoning by allowing DNS resolvers to validate that responses originate from the authoritative DNS server and have not been modified in transit. While DNSSEC does not encrypt DNS traffic, it ensures that DNS responses are trustworthy.

---

# Key Takeaways

- Route 53 can register and manage internet domains.
- Every domain is associated with a Hosted Zone containing DNS records.
- Domains progress through a lifecycle from registration to expiration.
- Auto-renewal helps prevent accidental domain loss.
- DNSSEC digitally signs DNS records to improve security.
- Route 53 supports DNSSEC signing for Hosted Zones.
- Protecting domains and DNS infrastructure is a critical aspect of production cloud security.