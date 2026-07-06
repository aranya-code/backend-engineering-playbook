# Hosted Zones

A hosted zone is a container for DNS records that define how traffic should be routed for a specific domain and its subdomains. It is the fundamental organizational unit in Amazon Route 53, analogous to a traditional DNS zone file. Every domain managed by Route 53 requires at least one hosted zone.

---

## Hosted Zone Architecture

When you create a hosted zone, Route 53 automatically assigns a set of four name servers (a delegation set) and creates two default records: an NS record and an SOA record.

```text
┌─────────────────────────────────────────────────────────────────┐
│                     Domain: example.com                         │
│                          │                                      │
│                          ▼                                      │
│              ┌───────────────────────┐                          │
│              │    Hosted Zone        │                          │
│              │   (Zone ID: Z1234)    │                          │
│              └───────────┬───────────┘                          │
│                          │                                      │
│         ┌────────────────┼────────────────┐                     │
│         │                │                │                     │
│         ▼                ▼                ▼                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  NS Record  │  │  SOA Record │  │  A Record   │             │
│  │ (auto)      │  │ (auto)      │  │ (user)      │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│         │                                    │                  │
│         ▼                                    ▼                  │
│  ┌─────────────┐                      ┌─────────────┐          │
│  │ 4 Name      │                      │  CNAME, MX, │          │
│  │ Servers     │                      │  TXT, AAAA  │          │
│  │ (Delegation │                      │  ... more    │          │
│  │  Set)       │                      │  records     │          │
│  └─────────────┘                      └─────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

- Route 53 assigns a unique **Hosted Zone ID** (e.g., `Z1234ABCDEF`) to each zone
- The NS record contains the four authoritative name servers for the zone
- The SOA record defines the primary name server, admin contact, and zone serial number
- You add custom records (A, AAAA, CNAME, MX, TXT, etc.) to route traffic

---

## Public vs Private Hosted Zones

Route 53 supports two types of hosted zones, each serving fundamentally different use cases.

### Public Hosted Zones

- Contain records that define how to route traffic **on the public internet**
- Accessible from anywhere — any DNS resolver worldwide can query these records
- Created automatically when you register a domain through Route 53
- Require the domain's registrar NS records to point to the hosted zone's delegation set
- Support all Route 53 routing policies (simple, weighted, latency, failover, geolocation, multi-value, geoproximity)

### Private Hosted Zones

- Contain records that define how to route traffic **within one or more VPCs**
- Only accessible from associated VPCs — invisible to the public internet
- Require **enableDnsSupport** and **enableDnsHostnames** set to `true` on associated VPCs
- Allow internal service discovery without exposing DNS records externally
- Can use the same domain name as a public hosted zone (split-view DNS)
- Support association with VPCs across multiple AWS accounts

### Comparison Table

| Feature                  | Public Hosted Zone                     | Private Hosted Zone                       |
|--------------------------|----------------------------------------|-------------------------------------------|
| **Accessibility**        | Internet-wide                          | Within associated VPCs only               |
| **DNS Resolution**       | Any public DNS resolver                | VPC-provided DNS resolver (AmazonProvidedDNS) |
| **Use Cases**            | Public websites, APIs, email           | Internal microservices, databases, tools  |
| **VPC Association**      | Not required                           | Required (at least one VPC)               |
| **Internet Access**      | Yes                                    | No (records not resolvable from internet) |
| **Domain Registration**  | Domain must be registered              | No registration required                  |
| **Health Checks**        | Fully supported                        | Not supported                             |
| **Routing Policies**     | All policies supported                 | Simple, weighted, latency, failover, multi-value |
| **DNSSEC Signing**       | Supported                              | Not supported                             |
| **Cost (per zone/month)**| $0.50                                  | $0.50                                     |

---

## VPC Association for Private Hosted Zones

A private hosted zone must be associated with at least one VPC. You can associate a single private hosted zone with multiple VPCs, even across different regions and accounts.

```text
┌─────────────────────────────────────────────────────────────┐
│               Private Hosted Zone                           │
│              internal.example.com                           │
│                                                             │
│   Records:                                                  │
│     api.internal.example.com  →  10.0.1.50                  │
│     db.internal.example.com   →  10.0.2.100                 │
│     cache.internal.example.com → 10.0.3.25                  │
└──────────────┬──────────────────┬───────────────────────────┘
               │                  │
      ┌────────▼────────┐  ┌─────▼──────────┐
      │   VPC-A          │  │   VPC-B         │
      │   us-east-1      │  │   eu-west-1     │
      │   10.0.0.0/16    │  │   10.1.0.0/16   │
      │                  │  │                  │
      │  ┌────────────┐  │  │  ┌────────────┐ │
      │  │ EC2: App    │  │  │  │ EC2: App   │ │
      │  │ Server      │  │  │  │ Server     │ │
      │  │             │  │  │  │            │ │
      │  │ Resolves:   │  │  │  │ Resolves:  │ │
      │  │ api.internal│  │  │  │ db.internal│ │
      │  │ .example.com│  │  │  │ .example   │ │
      │  │  → 10.0.1.50│  │  │  │ .com       │ │
      │  └────────────┘  │  │  │ → 10.0.2   │ │
      │                  │  │  │   .100      │ │
      └──────────────────┘  │  └────────────┘ │
                            └─────────────────┘
```

### VPC Association Requirements

- VPC must have `enableDnsSupport = true`
- VPC must have `enableDnsHostnames = true`
- For cross-account association, you must use the `CreateVPCAssociationAuthorization` API from the hosted zone owner account, then call `AssociateVPCWithHostedZone` from the VPC owner account
- A VPC can be associated with multiple private hosted zones
- Overlapping domain names across multiple private hosted zones follow the **most specific match** rule

---

## Delegation Sets

A delegation set is the collection of four name servers that Route 53 assigns to a hosted zone. These name servers are authoritative for all DNS queries to that zone.

```text
  Hosted Zone: example.com
  ┌─────────────────────────────────────┐
  │  Delegation Set                     │
  │                                     │
  │   ns-512.awsdns-00.net              │
  │   ns-1024.awsdns-00.org            │
  │   ns-0.awsdns-00.com               │
  │   ns-1536.awsdns-00.co.uk          │
  │                                     │
  │   (One NS per TLD for resilience)   │
  └─────────────────────────────────────┘
```

- Each delegation set contains exactly **four name servers**
- Name servers are distributed across four different TLDs (`.com`, `.net`, `.org`, `.co.uk`) for fault tolerance
- By default, Route 53 assigns a **random** delegation set to each new hosted zone

### Reusable Delegation Sets

A reusable delegation set allows you to assign the **same four name servers** to multiple hosted zones. This is particularly useful for white-label DNS and migration scenarios.

**Benefits:**
- Simplifies domain migrations — you configure the registrar NS records once for the delegation set, then create/delete hosted zones without updating NS records
- Enables white-label DNS services where a consistent set of name servers is needed
- Reduces operational overhead when managing hundreds of hosted zones

**Limitations:**
- Can only be created via the Route 53 API or CLI (not available in the console)
- Maximum of one reusable delegation set per AWS account (soft limit, can be increased)
- Cannot be converted from a standard delegation set — must create the hosted zone with the reusable set from the start

```bash
# Create a reusable delegation set
aws route53 create-reusable-delegation-set \
  --caller-reference "my-delegation-set-2024"

# Create a hosted zone using the reusable delegation set
aws route53 create-hosted-zone \
  --name example.com \
  --caller-reference "example-com-zone" \
  --delegation-set-id "/delegationset/N1234567890ABC"
```

---

## Split-View DNS

Split-view (split-horizon) DNS allows you to serve different DNS responses for the same domain name depending on whether the query originates from the public internet or from within your VPCs.

```text
                    example.com
                         │
            ┌────────────┴────────────┐
            │                         │
            ▼                         ▼
  ┌──────────────────┐     ┌──────────────────┐
  │  PUBLIC Hosted   │     │  PRIVATE Hosted   │
  │  Zone            │     │  Zone             │
  │                  │     │  (VPC-associated)  │
  │  api.example.com │     │  api.example.com  │
  │  → 54.23.1.100   │     │  → 10.0.1.50      │
  │  (Public ALB IP) │     │  (Internal ALB IP) │
  └──────────────────┘     └──────────────────┘
            │                         │
            ▼                         ▼
  ┌──────────────────┐     ┌──────────────────┐
  │  Internet Users  │     │  VPC Resources   │
  │  → Public ALB    │     │  → Internal ALB  │
  │  → WAF/CDN       │     │  → Direct access │
  │  → TLS termination│    │  → Lower latency │
  └──────────────────┘     └──────────────────┘
```

### How Split-View Works

- Create a **public hosted zone** for `example.com` with public-facing records
- Create a **private hosted zone** for `example.com` associated with your VPCs
- DNS queries from within associated VPCs resolve against the **private zone first**
- DNS queries from the public internet resolve against the **public zone**
- Both zones are fully independent — different records, different TTLs, different routing policies

### Common Split-View Patterns

- **API endpoints**: Public users hit a CDN/WAF, internal services connect directly
- **Databases**: Internal-only records for RDS endpoints, no public exposure
- **Testing**: Internal overrides that point staging domains to test environments

---

## Cross-Account Hosted Zone Sharing

Organizations often centralize DNS management in a shared-services account while allowing workload accounts to resolve private DNS records.

```text
  ┌───────────────────────────────────┐
  │  Account A (DNS Owner)            │
  │                                   │
  │  Private Hosted Zone:             │
  │  internal.corp.com                │
  │                                   │
  │  1. CreateVPCAssociation          │
  │     Authorization                 │
  │     (authorize VPC-B)             │
  └──────────────┬────────────────────┘
                 │  Authorization Token
                 ▼
  ┌───────────────────────────────────┐
  │  Account B (Workload Account)     │
  │                                   │
  │  VPC-B (10.1.0.0/16)             │
  │                                   │
  │  2. AssociateVPCWithHostedZone    │
  │     (associate VPC-B with         │
  │      Account A's hosted zone)     │
  │                                   │
  │  3. EC2 instances in VPC-B can    │
  │     now resolve:                  │
  │     api.internal.corp.com         │
  │     db.internal.corp.com          │
  └───────────────────────────────────┘
```

### Cross-Account Workflow

1. **Account A** (zone owner) calls `CreateVPCAssociationAuthorization` specifying the hosted zone ID and Account B's VPC ID/region
2. **Account B** (VPC owner) calls `AssociateVPCWithHostedZone` specifying the hosted zone ID and its own VPC
3. **Account A** should call `DeleteVPCAssociationAuthorization` to revoke the one-time authorization after association is complete
4. DNS resolution for the private hosted zone is now available within Account B's VPC

### Best Practices for Cross-Account DNS

- Use **AWS RAM** (Resource Access Manager) for sharing Route 53 Resolver rules at scale
- Centralize private hosted zones in a **shared-services** or **networking** account
- Implement **Route 53 Resolver endpoints** for hybrid DNS resolution between on-premises and AWS
- Clean up authorization tokens after association to prevent unauthorized future associations
- Use **AWS Organizations** integration for simplified multi-account DNS management

---

## Real-World Examples

### Example 1: Public Website

```text
Public Hosted Zone: myapp.com

  myapp.com           A     ALIAS → d1234.cloudfront.net (CloudFront)
  www.myapp.com       CNAME       → myapp.com
  api.myapp.com       A     ALIAS → my-alb-1234.us-east-1.elb.amazonaws.com
  mail.myapp.com      MX    10    → inbound-smtp.us-east-1.amazonaws.com
  myapp.com           TXT         → "v=spf1 include:amazonses.com ~all"
```

- CloudFront distribution serves the static frontend
- ALB handles API traffic with path-based routing
- SES manages email with MX and SPF records

### Example 2: Internal Microservices

```text
Private Hosted Zone: internal.myapp.com (VPCs: vpc-prod, vpc-staging)

  auth.internal.myapp.com       A   → 10.0.1.50   (Auth service NLB)
  orders.internal.myapp.com     A   → 10.0.2.100  (Orders service NLB)
  payments.internal.myapp.com   A   → 10.0.3.75   (Payments service NLB)
  redis.internal.myapp.com      CNAME → my-redis.abc123.cache.amazonaws.com
  postgres.internal.myapp.com   CNAME → my-db.abc123.us-east-1.rds.amazonaws.com
```

- Services discover each other via DNS rather than hardcoded IPs
- Database endpoints are abstracted behind friendly CNAME records
- Failover can be managed by updating DNS records without application changes

### Example 3: Split-View DNS for Hybrid Architecture

```text
Public Zone: corp.com
  vpn.corp.com        A     → 54.10.20.30  (VPN gateway public IP)
  www.corp.com        A     ALIAS → ALB (public)

Private Zone: corp.com (VPCs: vpc-prod, vpc-corp)
  vpn.corp.com        A     → 10.0.0.1    (VPN gateway private IP)
  www.corp.com        A     → 10.0.5.100  (Internal web server)
  jira.corp.com       A     → 10.0.6.50   (Internal Jira)
  wiki.corp.com       A     → 10.0.6.51   (Internal Confluence)
```

- Employees inside the VPC access internal tools directly via private IPs
- External users hit public endpoints through the internet-facing ALB
- VPN endpoint resolves to the private IP internally, avoiding hairpin routing

---

## Pricing

| Component                         | Cost                          | Notes                                          |
|-----------------------------------|-------------------------------|-------------------------------------------------|
| **Hosted zone (first 25)**        | $0.50 per zone / month        | Both public and private zones                   |
| **Hosted zone (above 25)**        | $0.10 per zone / month        | Volume discount kicks in                        |
| **Standard queries (first 1B)**   | $0.40 per million queries     | Public hosted zones                             |
| **Standard queries (above 1B)**   | $0.20 per million queries     | Public hosted zones                             |
| **Latency-based routing queries** | $0.60 per million queries     | Higher cost for advanced routing                |
| **Geo DNS queries**               | $0.70 per million queries     | Geolocation and geoproximity routing            |
| **Private hosted zone queries**   | No additional query charge    | Covered by VPC DNS resolution                   |
| **Health checks (basic)**         | $0.50 per health check / month| HTTP/HTTPS/TCP, 30-second interval              |
| **Health checks (advanced)**      | $0.75 per health check / month| String matching, HTTPS, 10-second interval      |
| **Domain registration**           | Varies by TLD                 | `.com` ≈ $13/year, `.io` ≈ $39/year             |

> **Cost optimization tip**: Delete hosted zones you are no longer using. Even an empty hosted zone incurs $0.50/month. For private zones, query charges are bundled with VPC DNS — no per-query billing.

---

## When to Use Which Type

### Use a Public Hosted Zone When:

- You need DNS records accessible from the public internet
- You are hosting a public-facing website, API, or email service
- You need health checks and DNS failover for high availability
- You require DNSSEC for domain validation and security
- You need advanced routing policies (geolocation, geoproximity)

### Use a Private Hosted Zone When:

- You need internal DNS resolution within your VPCs
- You want to implement service discovery for microservices
- You need to override public DNS with internal-only records (split-view)
- You want to expose friendly DNS names for RDS, ElastiCache, or internal NLBs
- You need cross-VPC or cross-account DNS resolution without internet exposure

---

## Key Takeaways

- A **hosted zone** is the fundamental container for DNS records in Route 53 — one zone per domain (minimum)
- **Public hosted zones** serve DNS to the entire internet; **private hosted zones** resolve only within associated VPCs
- Private hosted zones require VPCs with `enableDnsSupport` and `enableDnsHostnames` set to `true`
- **Split-view DNS** uses one public and one private hosted zone for the same domain to serve different records based on query origin
- **Delegation sets** are the four name servers assigned to a zone; **reusable delegation sets** let you share the same NS across multiple zones
- Cross-account private hosted zone sharing uses a two-step authorization/association workflow
- Health checks are **only available for public hosted zones** — private zones do not support them
- Private hosted zone queries have **no per-query charge** — they are included in VPC DNS pricing
- DNSSEC signing is **only supported for public hosted zones**
- When multiple private hosted zones have overlapping domains, Route 53 uses the **most specific match**
- A hosted zone that is deleted within 12 hours of creation is not billed
- Use Route 53 Resolver endpoints for **hybrid DNS** between on-premises networks and AWS VPCs
