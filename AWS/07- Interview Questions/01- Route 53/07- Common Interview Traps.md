# 07- Common Interview Traps

## Overview

Route 53 interview questions often appear simple because DNS itself is familiar. The difficulty at senior level is understanding the operational behavior behind DNS: resolver caching, TTLs, routing policies, health checks, private hosted zones, delegation, DNSSEC, failover, and the difference between DNS-level routing and request-level load balancing.

Interviewers commonly use these topics to expose shallow understanding. A strong answer should explain not only **what Route 53 does**, but also **why the behavior exists, what limitations it has, and how it affects production systems**.

The most important mental model is:

```text
Client
  │
  │ DNS query
  ▼
Recursive Resolver
  │
  │ cached?
  ├─────────────── Yes ──► Cached DNS Answer
  │
  No
  │
  ▼
Authoritative DNS
  │
  ▼
Route 53
  │
  ▼
DNS Answer
  │
  ▼
Recursive Resolver Cache
  │
  ▼
Client
```

A DNS change therefore does not necessarily reach every client immediately. The authoritative record can be correct while users continue receiving an older cached answer.

---

## The Core Mental Models Interviewers Expect

Before looking at individual traps, keep these distinctions clear:

| Concept | What it actually controls |
|---|---|
| Route 53 | Authoritative DNS and DNS-level routing |
| Recursive resolver | Resolves names on behalf of clients and caches responses |
| TTL | How long a DNS answer may remain cached |
| Health check | Determines whether a Route 53 endpoint is considered healthy |
| Routing policy | Determines which DNS answer Route 53 returns |
| Load balancer | Handles network/application traffic after DNS resolution |
| Private hosted zone | DNS namespace accessible through associated VPCs |
| DNSSEC | Protects DNS data integrity and authenticity |
| TLS | Protects application connections |
| CloudFront | Edge delivery and caching |
| API Gateway / ALB | Application/network traffic entry point |

A large percentage of Route 53 interview mistakes come from confusing these layers.

---

## DNS and Route 53 Traps

### Trap: Route 53 Is a Load Balancer

**Weak answer:**

> Route 53 distributes traffic between servers.

**Better answer:**

> Route 53 is a DNS service. Its routing policies influence the DNS responses returned to clients. The actual application connection happens after DNS resolution. A load balancer operates on the resulting network connection and can distribute individual requests or connections across backend targets.

The difference is important:

```text
DNS-level routing:

Client
  │
  │ DNS query
  ▼
Route 53
  │
  ▼
10.0.1.10
  │
  ▼
Client connects directly


Request-level load balancing:

Client
  │
  ▼
ALB
  │
  ├── Target A
  ├── Target B
  └── Target C
```

---

### Trap: Weighted Routing Gives Exact Traffic Percentages

Suppose Route 53 has:

```text
Region A → Weight 90
Region B → Weight 10
```

It is incorrect to say:

> Exactly 90% of HTTP requests will go to Region A.

The weights influence DNS responses. Recursive resolvers, client DNS caches, connection reuse, and different query patterns affect actual application traffic.

The correct interpretation is:

> Route 53 uses the configured weights when selecting DNS responses among weighted records. The resulting application traffic distribution is not guaranteed to exactly match those percentages.

---

### Trap: Lowering TTL Makes DNS Changes Instant

A common answer is:

> Set TTL to 1 second and the DNS change becomes immediate.

That is too simplistic.

A DNS response can already be cached by:

- Recursive resolvers.
- Operating systems.
- Browsers.
- Local DNS infrastructure.
- Application-level DNS caches.

If an answer was cached before the TTL was reduced, lowering the TTL on the authoritative record does not retroactively invalidate that cached answer.

```text
T0:
Resolver receives:
api.example.com → 10.0.1.10
TTL = 300

T1:
Engineer changes Route 53:
api.example.com → 10.0.2.10
TTL = 30

Existing resolver cache:
10.0.1.10
│
└── May remain until its original TTL expires
```

The senior-level answer is:

> TTL controls future caching behavior; it does not purge existing cached DNS answers.

---

### Trap: DNS Changes Always Propagate Globally Immediately

Route 53 changes are made to the authoritative DNS configuration, but clients may still receive cached answers.

Distinguish:

```text
Authoritative state
        ≠
Resolver cache state
        ≠
Application connection state
```

When troubleshooting a DNS change, test from multiple recursive resolvers and locations.

---

## Hosted Zone Traps

### Trap: A Hosted Zone and a Domain Are the Same Thing

They are related but different.

A **domain name** is the namespace, such as:

```text
example.com
```

A **hosted zone** is the authoritative DNS container used to manage records for that namespace.

A hosted zone contains records such as:

```text
example.com
api.example.com
www.example.com
```

The domain registration and DNS hosting can also be handled by different providers.

---

### Trap: Creating a Hosted Zone Automatically Controls the Domain

Creating a Route 53 hosted zone does not automatically make it authoritative for the Internet.

The domain's delegation must point to the hosted zone's authoritative name servers.

Conceptually:

```text
Registrar
   │
   │ NS delegation
   ▼
Route 53 Name Servers
   │
   ▼
Hosted Zone
   │
   ├── A
   ├── AAAA
   ├── CNAME
   └── MX
```

If the registrar still delegates to another DNS provider, queries will not reach the new Route 53 hosted zone.

---

### Trap: Every DNS Record Belongs to One Hosted Zone Globally

Hosted zones are separate DNS management boundaries.

You can have:

```text
Public Hosted Zone
example.com
```

and:

```text
Private Hosted Zone
example.com
```

This enables split-horizon DNS.

---

## Public vs Private Hosted Zone Traps

### Trap: Private Hosted Zones Are Accessible From the Internet

They are not intended for public DNS resolution.

A private hosted zone is associated with VPCs.

```text
VPC
 │
 ├── EC2
 ├── ECS
 └── EKS
      │
      ▼
VPC DNS Resolver
      │
      ▼
Private Hosted Zone
```

A name such as:

```text
payments.internal.example.com
```

can resolve internally without exposing the record publicly.

---

### Trap: Private Hosted Zones Automatically Work Everywhere in AWS

A private hosted zone is associated with specific VPCs.

If an application runs in:

```text
VPC A
```

but the private hosted zone is associated only with:

```text
VPC B
```

the application may not resolve the expected private record.

For multi-VPC architectures, consider:

- VPC associations.
- Route 53 Resolver.
- Resolver endpoints.
- DNS forwarding.
- Shared networking architecture.
- AWS Organizations / multi-account architecture.

---

### Trap: Private DNS Is the Same as Service Discovery

They overlap but are not identical architectural concepts.

For example:

```text
orders.internal.example.com
```

could be manually managed through Route 53.

A service-discovery platform may dynamically register and deregister service instances.

The distinction matters in dynamic microservice environments.

---

## Alias Record Traps

### Trap: Alias and CNAME Are the Same

They solve related problems but have important differences.

| Feature | Alias | CNAME |
|---|---|---|
| AWS-specific | Yes | No |
| DNS standard record | No | Yes |
| Can point to AWS resources | Yes | Yes, where supported |
| Zone apex support | Yes | No |
| Additional DNS query in many cases | Avoided for supported AWS targets | Resolver follows target |
| TTL configured directly | AWS-managed behavior for alias targets | Yes |

A common AWS pattern is:

```text
example.com
     │
     ▼
Route 53 Alias
     │
     ▼
CloudFront / ALB
```

This is particularly important because a normal CNAME cannot be used at the zone apex:

```text
example.com
```

---

### Trap: CNAME Can Always Be Used at the Root Domain

It cannot be used as a normal DNS CNAME at the zone apex because the apex must contain required DNS records such as SOA and NS.

For AWS resources that support it, use an alias record.

---

## Health Check Traps

### Trap: Route 53 Health Checks Automatically Monitor Every Backend

They do not.

A health check must be configured and its behavior must match the actual failure model.

A health check can evaluate an endpoint, but that does not mean:

```text
Application is healthy
```

in every meaningful sense.

For example:

```text
HTTP 200
```

may be returned while:

- PostgreSQL is unavailable.
- Redis is unavailable.
- Kafka is unavailable.
- A critical dependency is failing.
- The application is serving degraded responses.

A production health endpoint should represent meaningful application health.

---

### Trap: A Health Check Passing Means the User Can Reach the Application

Not necessarily.

The health checker and the end user may have different network paths.

```text
Route 53 Health Checker
          │
          ▼
        ALB
          │
          ▼
       Backend

User
 │
 ▼
DNS
 │
 ▼
CloudFront / ALB
 │
 ▼
Backend
```

A health check can succeed while users experience failures caused by:

- Client routing.
- DNS caching.
- CDN behavior.
- Firewall rules.
- TLS problems.
- Regional connectivity.
- Application-specific errors.

---

### Trap: Health Checks Instantly Trigger DNS Failover

DNS failover is still subject to DNS caching.

Even if Route 53 detects:

```text
Primary = unhealthy
```

a resolver may still have a previously cached DNS answer.

Therefore:

```text
Health failure detected
        ↓
Route 53 changes DNS response behavior
        ↓
Resolver cache expires
        ↓
Client performs DNS resolution
        ↓
New endpoint returned
```

Failover is not equivalent to instant connection migration.

---

### Trap: Health Checks Are the Same as Load Balancer Health Checks

They operate at different layers.

| Mechanism | Purpose |
|---|---|
| Route 53 health check | DNS routing decision |
| ALB target health | Determines backend target eligibility |
| Kubernetes readiness probe | Determines pod/service readiness |
| Kubernetes liveness probe | Detects process/container health |
| Application health endpoint | Represents application state |

These checks may be complementary.

---

## Failover Traps

### Trap: Route 53 Failover Automatically Replicates the Application

It does not.

Route 53 can help select a healthy endpoint:

```text
Primary Region
     X
     │
     ▼
Route 53
     │
     ▼
Secondary Region
```

But the secondary region must already have:

- Application infrastructure.
- Database strategy.
- Configuration.
- Secrets.
- Networking.
- Deployment artifacts.
- Required dependencies.
- Monitoring.

DNS is only one layer of disaster recovery.

---

### Trap: DNS Failover Terminates Existing Connections

DNS does not control existing TCP or TLS connections.

If a client already connected to:

```text
10.0.1.10
```

changing DNS does not move that connection to:

```text
10.0.2.10
```

The new DNS answer affects future resolution.

---

## Routing Policy Traps

### Trap: Latency-Based Routing Means Geographically Closest Region

Latency-based routing selects the AWS Region that Route 53 estimates will provide the lowest latency from the DNS query source.

It is not simply:

```text
User is in India
→ Mumbai must always win
```

The routing decision depends on observed network latency characteristics and available AWS Regions.

---

### Trap: Geolocation and Latency Routing Are the Same

They are not.

| Policy | Primary decision |
|---|---|
| Latency | Lowest estimated latency |
| Geolocation | Geographic location of the resolver/client context |
| Geoproximity | Geographic relationship between resources and query origin, with bias support |
| Weighted | Configured weight |
| Failover | Health/status of primary and secondary |
| IP-based | Client IP-derived routing configuration |

A good interview answer explicitly distinguishes the policies.

---

### Trap: Geolocation Routing Always Identifies the Exact End User

DNS often sees the recursive resolver rather than the actual user's IP address.

Therefore geographic routing can have limitations.

The query path may be:

```text
User
  │
  ▼
ISP Recursive Resolver
  │
  ▼
Route 53
```

Route 53 may make routing decisions based on the information available from the DNS query path rather than having direct application-layer knowledge of the user.

---

### Trap: Multivalue Answer Routing Is a Full Load Balancer

Multivalue answer routing can return multiple healthy records, but it is still DNS.

It does not provide:

- Per-request routing.
- Connection draining.
- Application-aware balancing.
- Session management.
- Backend request retries.

Those are load-balancer or application-layer responsibilities.

---

## TTL Traps

### Trap: TTL Is a Guarantee

TTL is a caching directive, not a strict promise that every component will behave exactly according to the configured value.

Resolvers generally honor TTL semantics, but additional application and operating-system caching can complicate observed behavior.

---

### Trap: Always Use the Lowest Possible TTL

Very low TTLs can increase DNS query volume and may reduce caching efficiency.

A better strategy is:

| Environment | Typical approach |
|---|---|
| Frequently changing test environment | Lower TTL |
| Stable production endpoint | Moderate TTL |
| Planned migration | Temporarily lower TTL before the change |
| Highly stable infrastructure | Longer TTL can be appropriate |

The exact value should be chosen according to the failure and change model.

---

### Trap: Lower TTL Immediately Before an Emergency Migration

Suppose:

```text
Current TTL = 86400
```

and an outage occurs.

Changing it to:

```text
TTL = 30
```

does not remove the existing 24-hour cached answers.

TTL reduction should generally be performed **before** a planned DNS migration.

---

## NXDOMAIN Traps

### Trap: NXDOMAIN Means the Server Is Down

NXDOMAIN means the queried DNS name does not exist according to the authoritative DNS response.

It does not necessarily mean:

```text
Application server is down
```

Possible causes include:

- Missing record.
- Wrong hosted zone.
- Incorrect delegation.
- Typographical error.
- Missing private-zone association.
- Incorrect DNS suffix.
- Stale negative cache.

---

### Trap: Fixing the DNS Record Immediately Removes NXDOMAIN

Resolvers can negatively cache DNS responses.

A sequence may look like:

```text
Query:
api.example.com

Response:
NXDOMAIN

Resolver caches negative result

Engineer creates:
api.example.com → ALB

Client queries again

Resolver:
"Still cached as NXDOMAIN"
```

This is why a newly created record may appear unavailable for some time.

---

## Delegation Traps

### Trap: NS Records in Route 53 Are Enough

Not necessarily.

There are two important concepts:

```text
Parent zone
   │
   │ NS delegation
   ▼
Child authoritative servers
   │
   ▼
Hosted zone
```

The hosted zone's NS records must correspond to the delegation at the parent.

If the registrar points to another provider, Route 53 will not become authoritative merely because the hosted zone exists.

---

### Trap: Changing NS Records in the Hosted Zone Changes Delegation

Changing the NS records inside the child zone does not necessarily update the delegation at the parent.

Delegation is controlled by the parent zone / registrar relationship.

This is a frequent troubleshooting trap.

---

## DNSSEC Traps

### Trap: DNSSEC Encrypts DNS Traffic

DNSSEC does not encrypt DNS traffic.

It provides authenticity and integrity validation for DNS data.

```text
DNSSEC:
"Was this DNS response legitimately signed?"

TLS:
"Is this application connection encrypted and authenticated?"
```

They solve different problems.

---

### Trap: DNSSEC Replaces HTTPS

It does not.

A production web application still needs TLS:

```text
DNSSEC
  │
  └── DNS integrity

HTTPS/TLS
  │
  └── Application confidentiality + authentication
```

---

## Private Hosted Zone Troubleshooting Traps

### Trap: If `dig` Fails From My Laptop, the Private Hosted Zone Is Broken

A private hosted zone is designed for VPC-connected DNS resolution.

Running:

```bash
dig service.internal.example.com
```

from a public laptop does not prove the private DNS configuration is wrong.

Test from:

- EC2.
- ECS task.
- EKS pod.
- VPC-connected host.
- Appropriate Resolver endpoint.

---

### Trap: VPC Association Is Enough

Private DNS resolution also depends on VPC DNS configuration.

Relevant VPC attributes include:

- DNS resolution.
- DNS hostnames.

The resolver path must be functioning.

A useful troubleshooting sequence is:

```text
Client
  ↓
VPC DNS configuration
  ↓
Route 53 Resolver
  ↓
Private Hosted Zone association
  ↓
Record
```

---

## DNS Troubleshooting Traps

### Trap: `ping` Is the Best DNS Test

`ping` is not a DNS diagnostic tool.

Use tools that expose DNS behavior:

```bash
dig api.example.com
```

```bash
nslookup api.example.com
```

For authoritative information:

```bash
dig +trace api.example.com
```

To query a specific resolver:

```bash
dig @1.1.1.1 api.example.com
```

```bash
dig @8.8.8.8 api.example.com
```

Different resolvers can reveal caching or propagation differences.

---

### Trap: Testing Only One DNS Resolver Is Enough

A production incident can affect:

- ISP resolver.
- Corporate resolver.
- Public resolver.
- VPC resolver.
- DNS caching layer.

Compare multiple paths:

```text
Local Resolver
       │
       ├── Public Resolver A
       ├── Public Resolver B
       └── Authoritative DNS
```

If the authoritative answer is correct but one recursive resolver returns an old answer, the issue may be caching rather than Route 53 configuration.

---

## Alias and Health Check Traps

### Trap: Every Alias Record Supports the Same Health Behavior

Alias records have AWS-specific behavior depending on the target type.

Do not assume every AWS resource behaves identically.

When configuring:

```text
evaluate_target_health = true
```

understand what health information Route 53 can actually obtain from the selected AWS resource.

The important interview principle is:

> Understand the target's supported health semantics rather than assuming an alias automatically performs an application health check.

---

## Domain Registration Traps

### Trap: Route 53 Hosted Zones Require Route 53 Domain Registration

They do not.

A domain can be registered through one provider while its authoritative DNS is hosted in Route 53.

For example:

```text
Domain Registrar
       │
       │ NS delegation
       ▼
Route 53
       │
       ▼
Hosted Zone
```

This separation is important when migrating DNS without moving domain registration.

---

## Security Traps

### Trap: DNS Changes Are Low Risk

DNS changes can redirect production traffic.

For example:

```text
api.example.com
        │
        ▼
Attacker-controlled endpoint
```

Potential consequences include:

- Credential theft.
- Phishing.
- Session compromise.
- Data exfiltration.
- Service outage.

Treat Route 53 changes as privileged infrastructure changes.

Use:

- Least-privilege IAM.
- MFA.
- IaC.
- Pull-request review.
- Audit logging.
- Protected production deployment paths.

---

### Trap: DNSSEC Prevents DNS Hijacking in Every Situation

DNSSEC protects validation of signed DNS data, but it does not prevent every type of domain or account compromise.

An attacker who gains control over the authoritative DNS administration environment can still cause serious damage.

DNSSEC should be part of a broader security model.

---

## CloudFront and Route 53 Traps

### Trap: Route 53 Caches Application Content

Route 53 handles DNS responses.

CloudFront caches application content.

```text
Route 53
    │
    └── "Where should I connect?"

CloudFront
    │
    └── "Can I serve this content from cache?"
```

These are different layers.

---

### Trap: Changing Route 53 Immediately Purges CloudFront

It does not.

DNS caching and CloudFront object caching are separate mechanisms.

A migration may involve:

```text
DNS TTL
+
CloudFront cache behavior
+
Origin configuration
+
Application deployment
```

Treat each cache independently.

---

## Kubernetes and Route 53 Traps

### Trap: Kubernetes DNS and Route 53 Are the Same DNS System

They operate at different scopes.

Inside Kubernetes:

```text
Pod
 │
 ▼
CoreDNS
 │
 ▼
Kubernetes Service
```

For external DNS:

```text
Client
 │
 ▼
Route 53
 │
 ▼
AWS Load Balancer
 │
 ▼
Kubernetes
```

Kubernetes CoreDNS can also forward queries outside the cluster.

The architecture should distinguish:

- Cluster DNS.
- VPC DNS.
- Public authoritative DNS.
- Service discovery.

---

### Trap: Route 53 Should Handle Every Kubernetes Service

Not necessarily.

Internal Kubernetes services are usually better represented using Kubernetes-native service discovery.

Route 53 becomes more relevant for:

- Public endpoints.
- External service names.
- Cross-cluster DNS.
- Hybrid architectures.
- External service discovery requirements.

---

## Microservices Traps

### Trap: Every Microservice Should Have a Public Route 53 Record

That is usually poor architecture.

Internal services should generally remain private:

```text
Public API
   │
   ▼
Internal Service
   │
   ▼
Database
```

Exposing every service publicly increases:

- Attack surface.
- DNS management complexity.
- Security requirements.
- Operational overhead.

Use private DNS/service discovery where appropriate.

---

## Infrastructure as Code Traps

### Trap: DNS Can Be Changed Manually Because It Is Simple

DNS is infrastructure.

Manual changes create:

- Configuration drift.
- Poor auditability.
- Hard-to-reproduce environments.
- Deployment inconsistencies.
- Incident-response uncertainty.

Prefer:

```text
Git
 ↓
Pull Request
 ↓
Terraform Plan
 ↓
Review
 ↓
Apply
 ↓
Route 53
```

---

### Trap: Terraform Destroy Is Safe for DNS

Destroying a production hosted zone or important DNS record can cause an immediate availability incident.

Production DNS should have:

- Protected state.
- Restricted deployment permissions.
- Review requirements.
- Appropriate lifecycle controls.
- Backup/export strategy where necessary.

---

## Senior-Level Scenario Traps

### Scenario: Users Still Reach the Old Load Balancer After a DNS Change

Do not immediately conclude that Route 53 is broken.

Investigate:

```text
1. Authoritative Route 53 answer
2. Recursive resolver answer
3. DNS TTL
4. Client-side caching
5. Application DNS caching
6. Existing TCP/TLS connections
7. CDN behavior
```

Useful commands:

```bash
dig api.example.com
```

```bash
dig @1.1.1.1 api.example.com
```

```bash
dig @8.8.8.8 api.example.com
```

```bash
dig +trace api.example.com
```

---

### Scenario: Route 53 Failover Is Not Happening

Check:

```text
Health check status
        ↓
Health check target
        ↓
Routing policy
        ↓
Record association
        ↓
Resolver cache
        ↓
Client behavior
```

Do not stop at:

> The server is down.

The real question is:

> Is Route 53 currently returning the expected DNS response, and is the client actually querying DNS again?

---

### Scenario: Private DNS Works From EC2 but Not From EKS

Possible areas include:

- EKS pod DNS configuration.
- CoreDNS.
- VPC DNS.
- Network policies.
- Security controls.
- Private hosted zone association.
- Resolver behavior.
- Search domains.

The fact that EC2 works proves that the private zone may be correctly configured, but it does not prove that the Kubernetes DNS path is correct.

---

### Scenario: New Record Returns NXDOMAIN

Investigate:

```text
Record exists?
    │
    ├── No → Create/fix record
    │
    └── Yes
         │
         ▼
Correct hosted zone?
         │
         ▼
Correct NS delegation?
         │
         ▼
Correct resolver?
         │
         ▼
Negative cache expired?
```

Do not assume that creating the record immediately eliminates the problem.

---

## Common Interview Questions and Strong Answers

### Why doesn't a DNS change take effect immediately?

Because DNS answers are cached by recursive resolvers and potentially by clients. The authoritative record can change immediately while previously cached responses remain valid until their TTL expires.

### Can Route 53 route individual HTTP requests?

No. Route 53 makes DNS-level routing decisions. Individual HTTP request distribution is typically handled by services such as ALB, CloudFront, API Gateway, or the application itself.

### What happens when a Route 53 health check fails?

For routing configurations that use health checks, Route 53 can stop returning an unhealthy endpoint and select another eligible record according to the configured routing policy. Existing DNS caches may continue returning the old answer until they expire.

### Why can a DNS record exist but still return NXDOMAIN?

Possible reasons include:

- Query reaching the wrong authoritative zone.
- Incorrect NS delegation.
- Private hosted-zone association issues.
- Negative caching.
- Incorrect record name.

### What is the difference between latency and geolocation routing?

Latency routing attempts to select the Region associated with the lowest latency for the DNS query. Geolocation routing uses geographic routing rules to select answers based on geographic location.

### Why would you use a private hosted zone?

To provide DNS names for internal resources without exposing those records through public DNS.

### Does Route 53 health checking prove that an application is healthy?

Only to the extent represented by the configured health check. A simple HTTP success response may not reflect dependency health or business-level availability.

### Can Route 53 replace ALB?

No. They operate at different layers.

### Why would you use an alias instead of CNAME?

For supported AWS targets, alias records integrate with AWS resources and can be used at the zone apex, where a normal CNAME cannot be used.

### Does DNSSEC encrypt DNS?

No. DNSSEC provides authenticity and integrity validation for DNS data. It does not provide encryption.

---

## Interview Response Framework

When asked a Route 53 architecture question, avoid immediately naming a feature.

Use this reasoning pattern:

```text
Requirement
    ↓
DNS layer involved?
    ↓
Public or private?
    ↓
Routing requirement?
    ↓
Failure model?
    ↓
Caching / TTL implications?
    ↓
Security implications?
    ↓
Operational model?
    ↓
Route 53 feature
```

For example:

> We need active-passive multi-region failover.

A strong answer should progress through:

```text
Active-passive
     ↓
Two regional endpoints
     ↓
Route 53 failover routing
     ↓
Health checks
     ↓
Appropriate TTL
     ↓
Regional application readiness
     ↓
Database replication / DR
     ↓
Tested failover procedure
```

This demonstrates architecture thinking rather than memorization.

---

## What Senior Interviewers Usually Look For

A senior candidate should demonstrate that they understand the boundaries of Route 53.

| Topic | Expected understanding |
|---|---|
| DNS | Recursive vs authoritative resolution |
| TTL | Caching and stale answers |
| Routing | DNS-level, not request-level |
| Health checks | Routing decisions, not universal application health |
| Failover | DNS failover is not connection migration |
| Private DNS | VPC-scoped resolution |
| Alias | AWS integration and zone-apex behavior |
| NXDOMAIN | Negative caching and delegation |
| Security | DNS administration is privileged |
| DNSSEC | Integrity/authenticity, not encryption |
| DR | DNS is only one DR component |
| IaC | DNS should be managed as infrastructure |
| Multi-cloud | Provider independence vs operational complexity |
| Troubleshooting | Authoritative answer vs resolver answer |

---

## Key Takeaways

- Route 53 is an authoritative DNS service, not a traditional load balancer.
- DNS routing affects DNS responses, not individual HTTP requests.
- Weighted routing does not guarantee exact application traffic percentages.
- DNS TTL controls caching behavior; lowering TTL does not invalidate existing cached answers.
- DNS changes can appear delayed even when the Route 53 configuration is already correct.
- A hosted zone is not the same thing as domain registration or delegation.
- Creating a Route 53 hosted zone does not automatically make it authoritative for the domain.
- Private hosted zones require the correct VPC associations and working VPC DNS resolution.
- Route 53 health checks do not automatically represent complete application health.
- DNS failover does not terminate or migrate existing TCP/TLS connections.
- Latency routing, geolocation routing, weighted routing, and failover routing solve different problems.
- NXDOMAIN means the queried DNS name does not exist according to the relevant DNS authority; it does not directly mean the application server is down.
- Negative DNS caching can make a newly created record appear unavailable.
- Alias records and CNAME records have different semantics, especially at the zone apex.
- DNSSEC protects DNS data integrity and authenticity; it does not encrypt DNS or replace HTTPS.
- Route 53 should generally be treated as production infrastructure and managed through controlled automation.
- Kubernetes CoreDNS, VPC DNS, private hosted zones, and public Route 53 DNS operate at different layers.
- DNS troubleshooting should compare authoritative answers, recursive resolver answers, TTLs, delegation, and client behavior.
- A strong senior-level answer explains the **request lifecycle, failure mode, caching behavior, and operational consequences**, not just the Route 53 feature name.
- The most dangerous interview answer is an absolute statement such as **"DNS changes are immediate," "health checks mean the application is healthy," or "Route 53 distributes requests."**