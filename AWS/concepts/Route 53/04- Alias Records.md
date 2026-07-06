# Alias Records

Alias records are an AWS-specific extension to DNS functionality, exclusive to Amazon Route 53. They provide a way to map your domain name directly to AWS resources such as Elastic Load Balancers, CloudFront distributions, and S3 buckets. Unlike standard CNAME records, Alias records can be used at the zone apex (root domain) and Route 53 responds to Alias queries with the target resource's IP address directly, without any additional DNS resolution charge.

---

## How Alias Records Work

- Alias records are a Route 53-specific construct — they do not exist in the DNS RFC specification
- When a DNS resolver queries an Alias record, Route 53 internally resolves the target resource and returns the underlying IP address(es)
- The resolver never sees the intermediate target — it receives A or AAAA records directly
- This internal resolution happens transparently within Route 53's infrastructure, avoiding extra DNS lookups
- Alias records can be configured for record types: A, AAAA, CAA, CNAME, MX, NAPTR, PTR, SOA, SPF, SRV, TXT

### Alias Resolution Flow

```text
┌──────────────┐       ┌──────────────────┐       ┌─────────────────────┐
│  DNS Client  │──────▶│   DNS Resolver    │──────▶│   Route 53 Hosted   │
│  (Browser)   │       │  (Recursive)      │       │       Zone          │
└──────────────┘       └──────────────────┘       └─────────┬───────────┘
                                                            │
                                                   Query: example.com (A)
                                                            │
                                                            ▼
                                                  ┌─────────────────────┐
                                                  │  Route 53 Finds     │
                                                  │  Alias Record       │
                                                  │                     │
                                                  │  Target: ALB DNS    │
                                                  │  dualstack.my-alb.  │
                                                  │  us-east-1.elb.     │
                                                  │  amazonaws.com      │
                                                  └─────────┬───────────┘
                                                            │
                                                  Internal Resolution
                                                  (No extra DNS hop)
                                                            │
                                                            ▼
                                                  ┌─────────────────────┐
                                                  │  Route 53 Returns   │
                                                  │  A Record(s)        │
                                                  │                     │
                                                  │  52.23.186.100      │
                                                  │  52.23.186.101      │
                                                  │  52.23.186.102      │
                                                  └─────────────────────┘
                                                            │
                              ┌──────────────────────────────┘
                              ▼
                    Client receives IP(s)
                    directly — no CNAME
                    chain visible
```

- The client queries `example.com` as a standard A record
- Route 53 detects the Alias configuration and resolves the target internally
- The response contains only A records (IP addresses) — no CNAME indirection is exposed
- This entire resolution happens within a single DNS query/response cycle

---

## Alias vs CNAME — Detailed Comparison

| Feature                    | Alias Record                              | CNAME Record                             |
|----------------------------|-------------------------------------------|------------------------------------------|
| **Root domain support**    | ✅ Yes — works at zone apex               | ❌ No — RFC prohibits CNAME at apex      |
| **DNS query charges**      | ✅ Free for queries to AWS resources       | 💰 Standard Route 53 query charges apply |
| **Resolution speed**       | ⚡ Faster — resolved internally by R53    | 🐢 Slower — requires additional DNS hop  |
| **AWS integration**        | ✅ Deep — native health checks, failover  | ❌ None — treated as standard DNS        |
| **Health check support**   | ✅ Inherits target's health automatically  | ⚠️ Must configure separately             |
| **Record types supported** | A, AAAA (most common), plus others        | CNAME only                               |
| **TTL control**            | ❌ Cannot set — uses target resource TTL  | ✅ Full control over TTL value           |
| **Works outside AWS**      | ❌ Route 53 only                          | ✅ Any DNS provider                      |
| **Target flexibility**     | Limited to supported AWS resources        | Any domain name (AWS or non-AWS)         |
| **Visible in dig/nslookup**| Returns A/AAAA records directly           | Returns CNAME chain                      |

### Key Distinction

- **CNAME** says: "Go look up this other name instead" — the resolver does an additional lookup
- **Alias** says: "I already know the answer for that other name — here it is" — Route 53 does the lookup internally

---

## Supported Alias Targets

| Target Resource                          | Record Types | Notes                                              |
|------------------------------------------|--------------|----------------------------------------------------|
| **Elastic Load Balancer (ALB/NLB/CLB)**  | A, AAAA      | Most common use case; includes dualstack support    |
| **Amazon CloudFront Distribution**       | A, AAAA      | Must match alternate domain name (CNAME) in distro |
| **Amazon S3 Static Website Endpoint**    | A            | Bucket name must match the record name exactly      |
| **Amazon API Gateway (Regional/Edge)**   | A, AAAA      | Custom domain must be configured in API Gateway     |
| **AWS Global Accelerator**               | A, AAAA      | Maps to accelerator's static anycast IPs            |
| **Elastic Beanstalk Environment**        | A, AAAA      | Environment must have a CNAME prefix                |
| **VPC Interface Endpoint**               | A, AAAA      | For PrivateLink-powered services                    |
| **Another Route 53 Record (same zone)**  | A, AAAA      | Enables Alias chaining within the hosted zone       |

### Targets That Are NOT Supported

- ❌ EC2 instance public/private IP addresses directly
- ❌ RDS database endpoints (use CNAME instead)
- ❌ ElastiCache endpoints (use CNAME instead)
- ❌ ECS service endpoints directly
- ❌ Any non-AWS resource or arbitrary domain name
- ❌ Route 53 records in a different hosted zone (for most record types)

---

## Root Domain (Zone Apex) Support

One of the most critical advantages of Alias records is zone apex support. The DNS RFC (RFC 1034) explicitly prohibits CNAME records at the zone apex because the apex must coexist with SOA and NS records.

```text
Zone Apex Problem:

  example.com  ──▶  SOA record    (required by DNS spec)
  example.com  ──▶  NS records    (required by DNS spec)
  example.com  ──▶  CNAME record  (❌ CONFLICT — CNAME cannot coexist
                                      with any other record type)

Alias Solution:

  example.com  ──▶  SOA record    (required — no conflict)
  example.com  ──▶  NS records    (required — no conflict)
  example.com  ──▶  Alias (A)     (✅ Works — Alias is not a real CNAME,
                                      it's an internal Route 53 construct
                                      that returns A/AAAA records)
```

### Practical Example

```text
Scenario: Serving example.com from an ALB

Without Alias (broken):
  example.com  CNAME  my-alb-123.us-east-1.elb.amazonaws.com  ← ❌ Invalid

With Alias (works):
  example.com  A  ALIAS  my-alb-123.us-east-1.elb.amazonaws.com  ← ✅ Valid

With CNAME on subdomain (also works, but costs more):
  www.example.com  CNAME  my-alb-123.us-east-1.elb.amazonaws.com  ← ✅ Valid
```

- Without Alias, you would need to hardcode the ALB's IP addresses (which change dynamically) — this is unreliable and unsupported
- Alias records eliminate this problem entirely for the zone apex

---

## DNS Query Cost Comparison

Route 53 pricing for Alias queries targeting AWS resources is significantly different from standard record queries.

| Query Type                                  | Cost per Million Queries |
|---------------------------------------------|--------------------------|
| Alias to ELB, CloudFront, Elastic Beanstalk | **$0.00** (Free)         |
| Alias to S3 Website Endpoint                | **$0.00** (Free)         |
| Alias to API Gateway                        | **$0.00** (Free)         |
| Alias to another Route 53 record            | **$0.00** (Free)         |
| Standard A / AAAA / CNAME query             | **$0.40**                |
| Latency-based routing queries               | **$0.60**                |
| Geo DNS / Geoproximity queries              | **$0.70**                |

### Cost Impact at Scale

```text
Scenario: 100 million DNS queries/month for example.com → ALB

  Using CNAME (www.example.com only):
    100M × $0.40/M = $40.00/month

  Using Alias (example.com or www.example.com):
    100M × $0.00/M = $0.00/month

  Annual savings: $480.00 per domain
```

- For high-traffic domains, the cost savings from Alias records are substantial
- This pricing advantage applies only when the Alias target is a supported AWS resource
- If you combine Alias with routing policies (weighted, latency, etc.), the routing policy pricing applies

---

## Limitations and Constraints

### TTL Restrictions

- You **cannot** set a custom TTL on Alias records
- The TTL is automatically inherited from the target resource
- ELB targets typically return a TTL of 60 seconds
- CloudFront targets return a TTL of 60 seconds
- This lack of TTL control can impact caching strategies for DNS resolvers

### Cross-Account and Cross-Region Constraints

- Alias to an ELB works cross-region within the same account
- Alias to another Route 53 record must be in the **same hosted zone**
- Cross-account Alias to an ELB is supported but requires the target to be in a public hosted zone
- Private hosted zone Alias records can only target resources in the associated VPC region

### Target Restrictions

- Cannot Alias to an EC2 instance IP address — use an A record with the IP instead
- Cannot Alias to an RDS endpoint — use a standard CNAME record
- Cannot Alias to an arbitrary external domain (e.g., `api.stripe.com`)
- The Alias target must be a resource in the supported targets list

### Health Check Behavior

- Alias records **inherit** the health status of the target resource by default
- You can associate a Route 53 health check with an Alias record for additional control
- If the Alias target becomes unhealthy and you use failover routing, Route 53 will route to the secondary
- Health check evaluation adds no additional cost for Alias records

### Routing Policy Constraints

- When using Alias with weighted routing, all records in the group must be Alias or all must be non-Alias
- Mixing Alias and non-Alias records in the same routing policy group is not supported
- Alias records support all Route 53 routing policies: Simple, Weighted, Latency, Failover, Geolocation, Geoproximity, Multivalue Answer

---

## When to Use Alias vs CNAME — Decision Flowchart

```text
                    ┌─────────────────────────┐
                    │  Need to map a domain    │
                    │  to another endpoint?    │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Is the target an        │
              ┌─────│  AWS resource?           │─────┐
              │     └─────────────────────────┘     │
             YES                                    NO
              │                                     │
              ▼                                     ▼
    ┌───────────────────┐              ┌───────────────────┐
    │  Is it a supported │              │  Use CNAME         │
    │  Alias target?     │              │  (on subdomain)    │
    │  (ELB, CF, S3,    │              │                     │
    │   API GW, etc.)   │              │  or A record with   │
    └────────┬──────────┘              │  IP if at apex      │
             │                         └───────────────────┘
        ┌────┴────┐
       YES        NO
        │          │
        ▼          ▼
  ┌──────────┐  ┌──────────────┐
  │  Is it   │  │  Use CNAME    │
  │  at zone │  │  (subdomain)  │
  │  apex?   │  │  or A record  │
  └────┬─────┘  └──────────────┘
       │
  ┌────┴────┐
 YES        NO
  │          │
  ▼          ▼
┌──────┐  ┌─────────────────┐
│ MUST │  │  Prefer Alias    │
│ use  │  │  (free queries,  │
│Alias │  │   faster, native │
│      │  │   health checks) │
│      │  │                  │
│      │  │  Use CNAME only  │
│      │  │  if you need     │
│      │  │  custom TTL      │
└──────┘  └─────────────────┘
```

### Quick Decision Rules

- **Always use Alias** when the target is a supported AWS resource at the zone apex — it is the only option
- **Prefer Alias** for subdomains pointing to supported AWS targets — it is free, faster, and integrates with health checks
- **Use CNAME** when pointing to non-AWS resources (e.g., third-party CDNs, SaaS endpoints)
- **Use CNAME** when you need explicit control over TTL values
- **Use CNAME** when the target is an unsupported AWS resource (e.g., RDS, ElastiCache)
- **Use A record** when pointing to a static IP address (e.g., EC2 Elastic IP)

---

## Alias Record Configuration Example

### Creating an Alias to an ALB (AWS CLI)

```json
{
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "example.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z35SXDOTRQ7X7K",
          "DNSName": "dualstack.my-alb-1234567890.us-east-1.elb.amazonaws.com",
          "EvaluateTargetHealth": true
        }
      }
    }
  ]
}
```

- `HostedZoneId` — the hosted zone ID of the **target resource** (not your domain's hosted zone)
- Each AWS service has a fixed hosted zone ID per region (documented by AWS)
- `EvaluateTargetHealth` — when `true`, Route 53 checks target health before returning the record
- `DNSName` — the DNS name of the target AWS resource (typically includes `dualstack.` prefix for ELBs)

---

## Key Takeaways

- **Alias is AWS-proprietary** — it exists only in Route 53 and is not a standard DNS record type
- **Zone apex support** is the primary differentiator — CNAME cannot exist at the root domain per DNS RFC
- **Free queries** for Alias records pointing to AWS resources can save hundreds of dollars monthly at scale
- **Faster resolution** because Route 53 resolves the target internally without an extra DNS hop
- **No TTL control** — you cannot override the TTL on Alias records; it is inherited from the target resource
- **Limited targets** — only specific AWS resources are supported; you cannot Alias to arbitrary domains or EC2 IPs
- **Always prefer Alias** over CNAME when pointing to a supported AWS resource — there is no downside except TTL control
- **Health check integration** — Alias records automatically inherit target health, enabling seamless failover routing
- **Cross-account works** for ELB targets in public hosted zones but has restrictions in private zones
- **Interview tip** — Alias vs CNAME is one of the most frequently asked Route 53 questions in AWS certifications; focus on zone apex support, free pricing, and the list of supported targets
