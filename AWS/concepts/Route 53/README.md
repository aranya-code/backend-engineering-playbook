# Route 53

Amazon Route 53 — DNS management, domain registration, health checks, and traffic routing, from DNS fundamentals through production multi-region architectures. 30-part series.

---

## 📚 Core Concepts

| # | Topic | Description |
|---|-------|-------------|
| 01 | [Introduction](01-%20Introduction.md) | What Route 53 is, why the name, core features, and why it matters at a senior level |
| 02 | [DNS Fundamentals](02-%20DNS%20Fundamentals.md) | Foundational DNS concepts — resolution flow, recursive vs. authoritative, key terms |
| 03 | [Route 53 Architecture](03-%20Route%2053%20Architecture.md) | Global anycast network, shuffle sharding, and how the 100% SLA is achieved |
| 04 | [Hosted Zones](04-%20Hosted%20Zones.md) | Public vs. private zones, cross-account association, zone delegation |
| 05 | [DNS Record Types](05-%20DNS%20Record%20Types.md) | A, AAAA, CNAME, MX, TXT, NS, SOA, PTR, SRV, CAA — full reference |
| 06 | [Alias Records](06-%20Alias%20Records.md) | AWS-specific CNAME alternative — internals, zone apex support, supported targets |

## 🧭 Routing Policies

| # | Topic | Description |
|---|-------|-------------|
| 07 | [Simple and Weighted Routing](07-%20Routing%20Policies%20-%20Simple%20and%20Weighted.md) | Single-resource routing and traffic-percentage splitting for canary/blue-green deploys |
| 08 | [Latency-Based Routing](08-%20Routing%20Policies%20-%20Latency-Based.md) | Routing to the lowest-latency region based on resolver location |
| 09 | [Failover Routing](09-%20Routing%20Policies%20-%20Failover.md) | Primary/secondary health-checked failover |
| 10 | [Geolocation and Geoproximity](10-%20Routing%20Policies%20-%20Geolocation%20and%20Geoproximity.md) | Routing by user location, and distance-based routing with adjustable bias |
| 11 | [Multivalue Answer Routing](11-%20Routing%20Policies%20-%20Multivalue%20Answer.md) | Returning multiple healthy IPs for lightweight DNS-level load balancing |
| 12 | [Traffic Flow](12-%20Traffic%20Flow.md) | The visual policy editor for complex, layered routing logic |

## ⚙️ Operations

| # | Topic | Description |
|---|-------|-------------|
| 13 | [Health Checks](13-%20Health%20Checks.md) | HTTP/HTTPS/TCP/calculated checks, quorum-based failure detection |
| 14 | [DNS Failover Architecture](14-%20DNS%20Failover%20Architecture.md) | Active-passive and active-active DR patterns built on failover routing |
| 15 | [Domain Registration](15-%20Domain%20Registration.md) | Registering, transferring, and managing domains through Route 53 |
| 16 | [Route 53 Resolver](16-%20Route%2053%20Resolver.md) | Hybrid DNS — inbound/outbound endpoints for on-premises integration |
| 17 | [TTL and DNS Caching](17-%20TTL%20and%20DNS%20Caching.md) | Caching trade-offs, propagation reality, and migration TTL strategy |

## 🔌 Integrations

| # | Topic | Description |
|---|-------|-------------|
| 18 | [Route 53 with S3](18-%20Route%2053%20with%20S3.md) | Static website hosting via S3 website endpoints |
| 19 | [Route 53 with CloudFront](19-%20Route%2053%20with%20CloudFront.md) | Production-grade CDN + HTTPS in front of any origin |
| 20 | [Route 53 with ELB and ALB](20-%20Route%2053%20with%20ELB%20and%20ALB.md) | Routing to load-balanced application fleets |
| 21 | [Route 53 with API Gateway and Lambda](21-%20Route%2053%20with%20API%20Gateway%20and%20Lambda.md) | Custom domains for serverless APIs |

## 🎯 Production & Reference

| # | Topic | Description |
|---|-------|-------------|
| 22 | [Route 53 Security](22-%20Route%2053%20Security.md) | IAM, DNSSEC, query logging, and subdomain takeover prevention |
| 23 | [Troubleshooting](23-%20Troubleshooting.md) | Common issues — propagation delays, failover not triggering, IaC errors |
| 24 | [Advantages and Limitations](24-%20Advantages%20and%20Limitations.md) | Honest trade-offs of the service |
| 25 | [Route 53 vs Other DNS Solutions](25-%20Route%2053%20vs%20Other%20DNS%20Solutions.md) | vs. Cloudflare DNS, vs. Load Balancers, vs. CloudTrail/CloudWatch |
| 26 | [Monitoring and Best Practices](26-%20Monitoring%20and%20Best%20Practices.md) | What to monitor and why |
| 27 | [Cost Optimization](27-%20Cost%20Optimization.md) | Billing model and concrete cost levers |
| 28 | [Production Best Practices](28-%20Production%20Best%20Practices.md) | Operational discipline for production DNS |
| 29 | [Real-World Architectures](29-%20Real-World%20Architectures.md) | Six end-to-end architecture patterns |
| 30 | [Common Interview Questions](30-%20Common%20Interview%20Questions.md) | Beginner through senior-level Q&A |

---

## 🔗 See Also

- [`../`](../) — AWS concepts overview
- [`../../README.md`](../../README.md) — full AWS knowledge base

---

*Part of the [backend-engineering-playbook](../../../) knowledge base — Aranya Majumdar*
