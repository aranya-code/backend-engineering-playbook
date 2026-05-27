# Amazon Route 53

## Definition

Amazon Route 53 is a highly available and scalable DNS (Domain Name System) web service provided by AWS.

It is used for:
- Domain registration
- DNS management
- Health checking
- Traffic routing

---

# Simple Understanding

Think of Route 53 as the **internet phonebook**.

When a user types:

```bash
www.example.com
```

Route 53 helps convert it into an IP address:

```bash
3.110.24.5
```

So the browser knows where to connect.

---

# Why the Name Route 53?

- **Route** → Routes internet traffic
- **53** → DNS uses Port 53

---

# Core Features

| Feature | Purpose |
|---|---|
| Domain Registration | Buy and manage domains |
| DNS Management | Map domains to servers |
| Health Checks | Monitor application health |
| Traffic Routing | Intelligent request routing |
| Failover | Switch traffic automatically |
| Load Balancing | Distribute traffic |
| Hybrid DNS | AWS + On-Prem DNS integration |

---

# DNS Basics

## What is DNS?

DNS converts human-readable names into IP addresses.

Example:

```bash
google.com → 142.250.183.14
```

Without DNS, users would need to remember IP addresses.

---

# DNS Resolution Flow

```text
User
 ↓
Browser Cache
 ↓
OS Cache
 ↓
ISP DNS Resolver
 ↓
Root DNS Server
 ↓
TLD Server (.com)
 ↓
Route 53 Hosted Zone
 ↓
Application Server
```

---

# Important DNS Terms

| Term | Meaning |
|---|---|
| Domain | example.com |
| Subdomain | api.example.com |
| DNS Record | Mapping entry |
| Hosted Zone | Collection of DNS records |
| Nameserver | DNS server |
| TTL | DNS cache duration |
| Resolver | Performs DNS lookup |

---

# Hosted Zones

A Hosted Zone stores DNS records for a domain.

Example:

```bash
example.com
```

Contains:

```bash
www.example.com
api.example.com
mail.example.com
```

---

# Types of Hosted Zones

## 1. Public Hosted Zone

Accessible from the internet.

### Use Cases
- Public websites
- APIs
- Internet-facing applications

---

## 2. Private Hosted Zone

Accessible only inside a VPC.

### Use Cases
- Internal microservices
- Internal databases
- Corporate applications

---

# DNS Record Types

## 1. A Record

Maps domain to IPv4 address.

```bash
example.com → 3.110.24.5
```

---

## 2. AAAA Record

Maps domain to IPv6 address.

---

## 3. CNAME Record

Maps one domain to another domain.

```bash
api.example.com → myalb.amazonaws.com
```

### Limitation
Cannot be used on root domain.

---

## 4. Alias Record (AWS Special)

AWS-specific version of CNAME.

### Supports
- ALB
- CloudFront
- S3
- API Gateway

### Advantages
- Works at root domain
- Faster
- No extra DNS query charges for AWS resources

---

## 5. MX Record

Used for mail servers.

---

## 6. TXT Record

Stores text information.

### Common Uses
- SPF
- DKIM
- Domain verification

---

## 7. NS Record

Specifies authoritative nameservers.

---

## 8. PTR Record

Reverse DNS lookup.

```bash
IP → Domain
```

---

# Route 53 Routing Policies

---

## 1. Simple Routing

Routes traffic to a single resource.

### Example

```bash
example.com → EC2
```

---

## 2. Weighted Routing

Distributes traffic based on weights.

| Server | Weight |
|---|---|
| Version A | 80 |
| Version B | 20 |

### Use Cases
- A/B testing
- Canary deployments
- Blue-Green deployments

---

## 3. Latency Routing

Routes users to the nearest AWS Region.

### Example

| User Location | Region |
|---|---|
| India | Mumbai |
| USA | Virginia |
| Europe | Frankfurt |

### Benefits
- Lower latency
- Faster response time

---

## 4. Failover Routing

Primary + Backup setup.

### Flow

```text
Primary Server Healthy?
   YES → Route to Primary
   NO  → Route to Backup
```

### Use Cases
- Disaster Recovery
- High Availability

---

## 5. Geolocation Routing

Routes traffic based on user country.

### Example

| Country | Destination |
|---|---|
| India | indian-site.com |
| USA | us-site.com |

---

## 6. Geoproximity Routing

Routes users based on geographic distance.

Can manually shift traffic between regions.

---

## 7. Multi-Value Routing

Returns multiple healthy IPs.

Used for simple load balancing.

---

# Health Checks

Route 53 can monitor application endpoints.

### Example

```bash
https://myapp.com/health
```

If unhealthy:
- Removes endpoint from DNS
- Switches traffic to backup

---

# Health Check Types

| Type | Usage |
|---|---|
| HTTP | Website monitoring |
| HTTPS | Secure application monitoring |
| TCP | Database/server monitoring |

---

# Route 53 + ALB Architecture

```text
User
 ↓
Route 53
 ↓
Application Load Balancer
 ↓
EC2 Instances
```

---

# Route 53 + S3 Static Website

```text
Route 53
 ↓
S3 Static Website
```

### Steps
1. Create S3 bucket
2. Enable static website hosting
3. Create Alias record
4. Point domain to S3

---

# Route 53 + CloudFront

```text
User
 ↓
Route 53
 ↓
CloudFront
 ↓
S3 / ALB / EC2
```

### Benefits
- Caching
- Low latency
- DDoS protection

---

# Route 53 + Multi Region Setup

```text
India Users   → Mumbai
US Users      → Virginia
Europe Users  → Frankfurt
```

Using:
- Latency Routing
- Health Checks
- Failover Routing

---

# TTL (Time To Live)

Defines how long DNS responses are cached.

---

## Low TTL

```bash
60 seconds
```

### Benefits
- Faster DNS updates
- Faster failover

### Disadvantages
- More DNS queries

---

## High TTL

```bash
86400 seconds
```

### Benefits
- Fewer DNS queries
- Faster cached responses

### Disadvantages
- Slower propagation

---

# Route 53 Pricing

Charged for:
- Hosted zones
- DNS queries
- Health checks
- Domain registration

Usually low cost.

---

# Real World Architectures

## 1. Highly Available Application

```text
Route 53
 ↓
ALB
 ↓
Auto Scaling Group
 ↓
EC2 Instances
```

---

## 2. Disaster Recovery Setup

```text
Primary Region
Backup Region

Route 53 Failover Routing
```

---

## 3. Global SaaS Application

```text
India → Mumbai
US → Virginia
EU → Frankfurt
```

Using Latency Routing.

---

## 4. Blue-Green Deployment

```text
Blue  → Old Version
Green → New Version
```

Using Weighted Routing.

---

# Route 53 vs Load Balancer

| Route 53 | Load Balancer |
|---|---|
| DNS Service | Traffic Distribution |
| Global Routing | Request Handling |
| Domain Resolution | Layer 4/7 Balancing |

---

# Interview Questions

## Q1. What is Route 53?

Amazon Route 53 is a scalable DNS web service used for DNS management, domain registration, health checking, and intelligent traffic routing.

---

## Q2. Difference Between CNAME and Alias?

| CNAME | Alias |
|---|---|
| Standard DNS | AWS-specific |
| Cannot use root domain | Works on root domain |
| Extra DNS lookup | Faster |

---

## Q3. What is a Hosted Zone?

A container for DNS records of a domain.

---

## Q4. Difference Between Public and Private Hosted Zone?

| Public | Private |
|---|---|
| Internet accessible | VPC only |
| Public applications | Internal applications |

---

## Q5. Why Use Health Checks?

For automatic failover and high availability.

---

# Best Practices

| Best Practice | Reason |
|---|---|
| Use Alias records | Better AWS integration |
| Enable health checks | High availability |
| Use latency routing globally | Better performance |
| Use private hosted zones internally | Better security |
| Use low TTL during migrations | Faster DNS updates |

---

# Important AWS Services Used with Route 53

| Service | Usage |
|---|---|
| EC2 | Application hosting |
| ALB | Traffic distribution |
| CloudFront | CDN |
| S3 | Static website hosting |
| API Gateway | APIs |
| EKS/ECS | Container applications |

---

# One-Line Interview Definition

> Amazon Route 53 is a highly available and scalable DNS web service used for domain registration, DNS management, health checking, and intelligent traffic routing.
