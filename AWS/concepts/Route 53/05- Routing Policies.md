# Routing Policies

Routing policies determine how Amazon Route 53 responds to DNS queries for your domain. Each policy implements a different traffic management strategy, from simple single-endpoint routing to complex geographically-aware traffic distribution. Choosing the right routing policy is critical for achieving your application's availability, performance, and compliance requirements.

---

## Simple Routing

### How It Works

- Maps a domain name to one or more IP addresses or resources
- When multiple values are specified, Route 53 returns **all values** in a random order
- The **client** (typically the browser or resolver) chooses which address to use
- No health checks are associated with simple routing records
- Only **one record** of the same name and type can be created

```text
                        ┌─────────────────┐
   DNS Query            │                 │
   app.example.com ────►│    Route 53     │
                        │  Simple Routing │
                        │                 │
                        └────────┬────────┘
                                 │
                    Returns ALL values randomly
                                 │
                   ┌─────────────┼─────────────┐
                   ▼             ▼             ▼
              ┌─────────┐  ┌─────────┐  ┌─────────┐
              │ 1.2.3.4 │  │ 5.6.7.8 │  │ 9.0.1.2 │
              │ (EC2-A) │  │ (EC2-B) │  │ (EC2-C) │
              └─────────┘  └─────────┘  └─────────┘
                   │
                   ▼
           Client picks one
           (no server-side
            intelligence)
```

### Use Cases

- Single-resource deployments (one web server, one ALB)
- Development and staging environments
- Static websites with a single CloudFront distribution

### Configuration Considerations

- You cannot attach health checks to a simple routing record
- When returning multiple values, Route 53 does **not** filter unhealthy targets
- If you need health-check-aware multi-value responses, use **Multi-Value Answer** instead

### Gotchas / Limitations

- Client-side selection means you have **zero control** over which IP the client resolves to
- If one of the returned IPs is unhealthy, clients may still connect to it
- Not suitable for any production workload requiring high availability

---

## Weighted Routing

### How It Works

- Distributes traffic across multiple resources based on assigned **weights**
- Each record is assigned a numeric weight (0–255)
- The probability of a record being selected is: **`weight / sum_of_all_weights`**
- A weight of `0` stops traffic to that resource (unless all records are 0)
- Supports health checks — unhealthy records are excluded from the calculation

```text
   Weight Calculation Example:
   ──────────────────────────────────────────
   Record A: weight = 70   →  70/100 = 70%
   Record B: weight = 20   →  20/100 = 20%
   Record C: weight = 10   →  10/100 = 10%
                              ─────────────
                    Total:     100     100%

                        ┌─────────────────┐
   DNS Query            │                 │
   app.example.com ────►│    Route 53     │
                        │ Weighted Routing│
                        └────────┬────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │ 70%              │ 20%              │ 10%
              ▼                  ▼                  ▼
        ┌───────────┐     ┌───────────┐     ┌───────────┐
        │  v2.1.0   │     │  v2.2.0   │     │  v3.0.0   │
        │ (Stable)  │     │ (A/B Test)│     │ (Canary)  │
        │  ALB-1    │     │  ALB-2    │     │  ALB-3    │
        └───────────┘     └───────────┘     └───────────┘
```

### Canary Deployment Example

A typical canary rollout progression using weighted routing:

| Phase       | Stable Weight | Canary Weight | Canary Traffic | Duration    |
|-------------|---------------|---------------|----------------|-------------|
| Phase 1     | 99            | 1             | ~1%            | 30 min      |
| Phase 2     | 95            | 5             | ~5%            | 1 hour      |
| Phase 3     | 80            | 20            | ~20%           | 2 hours     |
| Phase 4     | 50            | 50            | ~50%           | 1 hour      |
| Full Rollout| 0             | 100           | 100%           | Permanent   |

### Use Cases

- **A/B testing** — route a percentage of users to a new feature variant
- **Canary deployments** — gradually shift traffic to a new application version
- **Blue/green deployments** — instant cutover by setting one weight to 0
- **Load distribution** across regions with unequal capacity

### Configuration Considerations

- Each weighted record must have a unique **Set ID** (identifier)
- Always attach health checks to avoid routing traffic to dead endpoints
- Weight changes propagate within the TTL window — set low TTLs (e.g., 60s) during active rollouts
- A record with weight `0` only receives traffic if **all other records** also have weight `0`

### Gotchas / Limitations

- Weighted routing is **probabilistic**, not deterministic — individual DNS responses are not guaranteed to match exact percentages
- DNS caching at the client/resolver level can skew observed traffic ratios
- Not a substitute for application-level traffic splitting (e.g., feature flags, service mesh)

---

## Latency-Based Routing

### How It Works

- Routes users to the AWS Region that provides the **lowest network latency**
- AWS continuously measures latency between end-user networks and each AWS Region
- Latency data is based on measurements from the **user's recursive resolver location**, not the user's exact IP
- You create one record per Region, and Route 53 evaluates latency at query time

```text
                         ┌──────────────────┐
                         │     Route 53     │
                         │  Latency-Based   │
                         └────────┬─────────┘
                                  │
            Evaluate latency from resolver to each region
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
         ▼                        ▼                        ▼
  ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
  │  us-east-1   │        │  eu-west-1   │        │ ap-south-1   │
  │  (Virginia)  │        │  (Ireland)   │        │  (Mumbai)    │
  │  ALB + EC2   │        │  ALB + EC2   │        │  ALB + EC2   │
  └──────┬───────┘        └──────┬───────┘        └──────┬───────┘
         │                       │                       │
         ▼                       ▼                       ▼
   Users in the            Users in             Users in Asia
   Americas               Europe/Africa         route here
   route here             route here

   ──────────────────────────────────────────────────────────
   User Location        Resolver Latency       Routed To
   ──────────────────────────────────────────────────────────
   New York, US         us-east-1: 12ms        us-east-1
                        eu-west-1: 85ms
                        ap-south-1: 210ms

   London, UK           us-east-1: 78ms        eu-west-1
                        eu-west-1: 8ms
                        ap-south-1: 120ms

   Mumbai, India        us-east-1: 195ms       ap-south-1
                        eu-west-1: 130ms
                        ap-south-1: 5ms
   ──────────────────────────────────────────────────────────
```

### Use Cases

- Global applications requiring the best possible user experience
- Multi-region active-active deployments
- Serving API responses from the closest regional backend

### Configuration Considerations

- Combine with health checks to automatically fail away from an unhealthy Region
- Latency is measured from the **DNS resolver's perspective**, not the end user — if a user uses a remote public DNS (e.g., 8.8.8.8), routing may be suboptimal
- You must deploy your application in multiple AWS Regions for this to be effective

### Gotchas / Limitations

- Latency measurements are **approximate** and can fluctuate
- Users with VPNs or remote DNS resolvers may be routed to non-optimal Regions
- Does not account for application-layer processing time — a Region with low network latency but overloaded servers will still receive traffic

---

## Failover Routing

### How It Works

- Implements an **active-passive** failover architecture
- You designate a **Primary** record and a **Secondary** record
- Route 53 continuously evaluates health checks on the Primary
- If the Primary is healthy, all traffic goes to it
- If the Primary fails its health check, traffic automatically shifts to the Secondary
- Health checks are **mandatory** on the Primary record

```text
   Normal Operation:
   ─────────────────────────────────────────────────────

                          ┌─────────────────┐
   DNS Query              │    Route 53     │
   app.example.com  ────► │   Failover      │
                          │   Routing       │
                          └───────┬─────────┘
                                  │
                     Health Check: ✅ HEALTHY
                                  │
                                  ▼
                          ┌──────────────┐
                          │   PRIMARY    │
                          │  us-east-1   │         ┌──────────────┐
                          │  ALB + EC2   │         │  SECONDARY   │
                          └──────────────┘         │  eu-west-1   │
                                                   │  (Standby)   │
                                                   └──────────────┘

   Failover Triggered:
   ─────────────────────────────────────────────────────

                          ┌─────────────────┐
   DNS Query              │    Route 53     │
   app.example.com  ────► │   Failover      │
                          │   Routing       │
                          └───────┬─────────┘
                                  │
                     Health Check: ❌ UNHEALTHY
                                  │
                                  ▼
                          ┌──────────────┐
                          │   PRIMARY    │
                          │  us-east-1   │         ┌──────────────┐
                          │   ╳ DOWN ╳   │ ──────► │  SECONDARY   │
                          └──────────────┘  auto   │  eu-west-1   │
                                           switch  │  (Now Active)│
                                                   └──────────────┘
```

### Use Cases

- Disaster recovery setups with a hot standby in another Region
- Failover to a static S3-hosted maintenance page
- Critical services requiring guaranteed availability during outages

### Configuration Considerations

- Health checks on the Primary record are **mandatory** — failover cannot function without them
- Health checks on the Secondary are optional but recommended to avoid failing over to a broken backup
- Set health check intervals to 10s (fast) for critical services (additional cost) vs. default 30s
- Consider using **calculated health checks** that aggregate multiple child checks

### Gotchas / Limitations

- Failover is **not instantaneous** — depends on health check interval + TTL propagation
- With default settings (30s interval, 3 failures, 60s TTL), worst-case failover time is ~150 seconds
- If both Primary and Secondary are unhealthy, Route 53 returns the Primary as a last resort
- Only supports **two endpoints** (primary and secondary) — use other policies for multi-endpoint failover

---

## Geolocation Routing

### How It Works

- Routes traffic based on the **geographic location** of the user (derived from source IP)
- You define routing rules at three granularity levels:
  - **Country** (e.g., US, DE, JP)
  - **Continent** (e.g., EU, NA, AS)
  - **US State** (for United States subdivisions)
- A **Default** record is required as a catch-all for locations without explicit rules
- Most specific match wins: State > Country > Continent > Default

```text
                        ┌──────────────────┐
                        │     Route 53     │
   DNS Query  ─────────►│   Geolocation    │
                        │     Routing      │
                        └────────┬─────────┘
                                 │
                    Evaluate user's geo location
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
    Location: US            Location: EU            Location: *
         │                       │                  (Default)
         ▼                       ▼                       │
  ┌──────────────┐       ┌──────────────┐                ▼
  │  us-east-1   │       │  eu-west-1   │        ┌──────────────┐
  │  English     │       │  GDPR        │        │ ap-south-1   │
  │  Content     │       │  Compliant   │        │  Fallback    │
  │  USD Pricing │       │  EUR Pricing │        │  Content     │
  └──────────────┘       └──────────────┘        └──────────────┘
```

### Use Cases

- **Content localization** — serve language-specific or region-specific content
- **Regulatory compliance** — ensure EU user data stays in EU Regions (GDPR)
- **Content licensing** — restrict media streaming to licensed geographies
- **Regional pricing** — display prices in local currency

### Configuration Considerations

- Always create a **Default** record — without it, users from unmapped locations receive `NXDOMAIN` (no answer)
- Geolocation is determined by IP-to-location databases, which are not 100% accurate
- Combine with health checks to fail over geo-located endpoints gracefully
- Overlapping rules follow the most-specific-wins priority

### Gotchas / Limitations

- Users behind VPNs or proxies will be routed based on the **exit node's location**, not their actual location
- IP geolocation databases can have inaccuracies, especially for mobile networks
- Does not support routing by city-level granularity
- Without a Default record, some users will get **no DNS response at all**

---

## Geoproximity Routing

### How It Works

- Routes traffic based on the geographic location of both **users and resources**
- Adds a **bias** value (-99 to +99) to expand or shrink the geographic area from which a resource attracts traffic
- Positive bias → resource attracts traffic from a **larger** geographic area
- Negative bias → resource attracts traffic from a **smaller** geographic area
- Resources can be AWS Regions or custom latitude/longitude coordinates (for on-premises)
- **Requires Route 53 Traffic Flow** (visual policy editor) to configure

```text
   Without Bias (equal coverage):
   ─────────────────────────────────────────────

   ◄────── us-east-1 ──────►◄────── eu-west-1 ──────►
   |                        |                        |
   |   Serves Western       |   Serves Eastern      |
   |   Hemisphere           |   Hemisphere           |
   |                        |                        |

   With Bias (us-east-1: +50, eu-west-1: -25):
   ─────────────────────────────────────────────

   ◄─────────── us-east-1 (+50) ──────────►◄── eu-west-1 (-25) ──►
   |                                       |                      |
   |   Expanded coverage area              |  Shrunk coverage     |
   |   Pulls traffic from farther east     |  Serves only nearby  |
   |                                       |                      |

   Bias Spectrum:
   ─────────────────────────────────────────────
   -99 ◄─── Shrink coverage ─── 0 ─── Expand coverage ───► +99
        (Serve almost nobody)       (Attract far-away users)
```

### Use Cases

- **Gradual regional migration** — shift traffic from one Region to another incrementally
- **Capacity-aware routing** — reduce bias on overloaded Regions, increase on underutilized ones
- **Hybrid cloud** — route to on-premises resources using lat/long coordinates with bias adjustments
- **Cost optimization** — bias traffic toward cheaper Regions

### Configuration Considerations

- Geoproximity routing is **only available through Traffic Flow** — you cannot configure it via standard record sets
- Traffic Flow policies incur additional cost (~$50/month per policy record)
- Bias changes take effect gradually as DNS TTLs expire across resolver caches
- For non-AWS resources, you must specify exact latitude and longitude

### Gotchas / Limitations

- Requires **Route 53 Traffic Flow**, adding cost and complexity
- Bias values are relative — the effect depends on the geographic distance between resources
- Cannot completely eliminate traffic to a resource using bias alone (use weight 0 or remove the record instead)
- The Traffic Flow visual editor is the only supported configuration method — no direct API/CLI support for the bias parameter outside of traffic policies

---

## Multi-Value Answer Routing

### How It Works

- Returns **up to 8 healthy records** in response to a DNS query
- Each record is independently associated with a **health check**
- Unhealthy records are automatically excluded from the response
- The client receives multiple IPs and can try alternatives if one fails
- Provides client-side load balancing with health-check filtering

```text
                          ┌─────────────────┐
   DNS Query              │    Route 53     │
   app.example.com  ────► │  Multi-Value    │
                          │  Answer Routing │
                          └───────┬─────────┘
                                  │
                 Evaluate health checks for all records
                                  │
        ┌──────┬──────┬──────┬──────┬──────┬──────┐
        │  ✅  │  ✅  │  ❌  │  ✅  │  ✅  │  ❌  │
        │ IP-1 │ IP-2 │ IP-3 │ IP-4 │ IP-5 │ IP-6 │
        └──────┴──────┴──────┴──────┴──────┴──────┘
                                  │
                    Return only healthy records
                                  │
                          ┌───────▼───────┐
                          │  DNS Response │
                          │  IP-1, IP-2,  │
                          │  IP-4, IP-5   │
                          │  (4 healthy)  │
                          └───────────────┘
                                  │
                          Client picks one
                          (tries others if
                           first fails)
```

### Use Cases

- Fleet of independent EC2 instances without a load balancer
- Simple client-side load distribution with health awareness
- Services where ELB is not practical (UDP workloads, non-HTTP services)

### Configuration Considerations

- Health checks are **strongly recommended** for every record — without them, Multi-Value behaves like Simple routing
- You can create up to 8 records with the same name and type
- Each record must have a unique **Set ID**
- TTL values affect how quickly clients pick up changes in the healthy record set

### Gotchas / Limitations

- **NOT a replacement for Elastic Load Balancing** — it operates at the DNS layer, not the connection layer
- No session affinity, connection draining, or cross-zone load balancing
- Maximum of **8 records** returned per query — cannot scale beyond that
- Health check evaluation has a delay — recently failed instances may still be returned briefly
- Clients may cache the DNS response and stick to a single IP for the duration of the TTL

---

## Routing Policy Comparison

| Policy         | Primary Use Case                        | Health Check Required? | Max Records Returned | Key Feature                          |
|----------------|-----------------------------------------|------------------------|----------------------|--------------------------------------|
| Simple         | Single resource / basic mapping         | ❌ No                  | All values           | Simplest configuration               |
| Weighted       | A/B testing, canary deployments         | ✅ Recommended         | 1 per query          | Proportional traffic distribution    |
| Latency-Based  | Global low-latency applications         | ✅ Recommended         | 1 per query          | Routes to lowest-latency Region      |
| Failover       | Disaster recovery (active-passive)      | ✅ Mandatory (Primary) | 1 per query          | Automatic failover to secondary      |
| Geolocation    | Compliance, content localization        | ✅ Recommended         | 1 per query          | Location-based (country/continent)   |
| Geoproximity   | Regional traffic shaping                | ✅ Recommended         | 1 per query          | Bias-adjustable geographic routing   |
| Multi-Value    | Client-side LB with health filtering    | ✅ Recommended         | Up to 8              | Returns multiple healthy IPs         |

---

## Routing Policy Selection Decision Tree

```text
   Start: How should Route 53 answer DNS queries?
   ═══════════════════════════════════════════════

   Do you have a single resource?
   │
   ├── YES ──► Use SIMPLE Routing
   │
   └── NO ──► Do you need to distribute traffic by percentage?
              │
              ├── YES ──► Use WEIGHTED Routing
              │           (A/B tests, canary deployments)
              │
              └── NO ──► Do you need the lowest latency for users?
                         │
                         ├── YES ──► Use LATENCY-BASED Routing
                         │           (Global apps, multi-region)
                         │
                         └── NO ──► Do you need active-passive failover?
                                    │
                                    ├── YES ──► Use FAILOVER Routing
                                    │           (DR, maintenance pages)
                                    │
                                    └── NO ──► Must you route by user location?
                                               │
                                               ├── YES ──► Do you need bias control
                                               │           or non-AWS resources?
                                               │           │
                                               │           ├── YES ──► GEOPROXIMITY
                                               │           │    (Traffic Flow required)
                                               │           │
                                               │           └── NO ──► GEOLOCATION
                                               │                (Country/continent rules)
                                               │
                                               └── NO ──► Do you want DNS-level
                                                          health-aware multi-IP?
                                                          │
                                                          ├── YES ──► MULTI-VALUE
                                                          │           ANSWER
                                                          │
                                                          └── NO ──► Re-evaluate
                                                                     requirements
```

---

## Combining Routing Policies

Route 53 supports **nested (alias) records** that allow you to chain routing policies together for complex architectures:

```text
   Example: Latency + Weighted (Canary per Region)
   ════════════════════════════════════════════════

   app.example.com
         │
         ▼ (Latency-Based)
   ┌─────────────────────────────────┐
   │                                 │
   ▼                                 ▼
   us-east-1.app.example.com        eu-west-1.app.example.com
         │                                 │
         ▼ (Weighted)                      ▼ (Weighted)
   ┌─────┴─────┐                    ┌─────┴─────┐
   │           │                    │           │
   ▼           ▼                    ▼           ▼
  v2.0       v3.0                  v2.0       v3.0
 (90%)      (10%)                 (95%)       (5%)
  ALB-1      ALB-2                ALB-3      ALB-4
```

### Common Combinations

| Outer Policy   | Inner Policy | Scenario                                         |
|----------------|--------------|--------------------------------------------------|
| Latency        | Weighted     | Per-region canary deployments for global apps     |
| Latency        | Failover     | Multi-region with per-region DR                   |
| Geolocation    | Weighted     | A/B testing within specific geographies           |
| Failover       | Weighted     | Primary does canary; secondary is full fallback   |

---

## Key Takeaways / Interview Notes

- Route 53 provides **7 routing policies**: Simple, Weighted, Latency-Based, Failover, Geolocation, Geoproximity, and Multi-Value Answer
- **Simple Routing** returns all values and lets the client choose — no health checks, no intelligence
- **Weighted Routing** uses the formula `weight / total_weight` — ideal for canary deployments and A/B testing
- **Latency-Based Routing** measures latency from the DNS resolver (not the end user) to each AWS Region
- **Failover Routing** requires a health check on the Primary — without it, failover will not trigger
- **Geolocation Routing** always needs a **Default record** — without it, unmapped users get no response
- **Geoproximity Routing** requires **Route 53 Traffic Flow** and supports bias values from -99 to +99
- **Multi-Value Answer** returns up to **8 healthy records** — it is NOT a replacement for ELB
- Routing policies can be **combined via alias records** to build layered traffic management (e.g., Latency + Weighted)
- Health checks are recommended for all policies except Simple — they enable automatic failover and record filtering
- DNS caching (TTL) affects how quickly routing changes propagate — lower TTLs during active changes, but expect higher query costs
- Geoproximity bias cannot fully eliminate traffic to a resource — use weight 0 or remove the record to stop all traffic
- Failover worst-case recovery time: `(health_check_interval × failure_threshold) + TTL` — optimize each parameter for your SLA
