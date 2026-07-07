# Route 53 Architecture

## Global Anycast Network

Route 53's nameservers run on a global anycast network — the same IP address is announced from many physical locations worldwide, and the network routes each query to the nearest healthy location automatically. This is a major reason Route 53 can offer a 100% availability SLA: there's no single point of failure, and BGP routing handles failover at the network layer before your application even knows a location had an issue.

## Four Nameservers, Four TLDs

Every hosted zone is assigned four nameservers, deliberately spread across four different top-level domains (e.g., `ns-1.awsdns-00.com`, `ns-2.awsdns-00.net`, `ns-3.awsdns-00.org`, `ns-4.awsdns-00.co.uk`). This is intentional: if an entire TLD had an outage, your zone would still be reachable through the other three.

## Shuffle Sharding

Route 53 uses a technique called **shuffle sharding** to assign nameserver sets. Rather than every hosted zone sharing the exact same four servers, Route 53 draws from a much larger pool and assigns each zone a different combination. The practical effect: even if a subset of the underlying infrastructure is degraded, the odds that *your specific combination* of four nameservers is entirely affected are very low, and other customers' issues are isolated from yours.

## Request Flow Through Route 53

```text
Client
 ↓
Anycast Network (nearest edge location)
 ↓
Route 53 Nameserver
 ↓
Hosted Zone Lookup
 ↓
Routing Policy Evaluation (if applicable)
 ↓
Health Check Status Check (if applicable)
 ↓
DNS Response Returned
```

Routing policy evaluation and health check status are both resolved **at query time** — Route 53 doesn't pre-compute a static answer; it decides the response dynamically based on current health check state, so failover can happen within the TTL window rather than requiring a manual DNS change.

## Why Architecture Matters Here

Understanding that routing decisions happen per-query (not per-zone-configuration) explains behavior that otherwise looks confusing — like why a failover can take effect before you've changed anything, purely because a health check flipped state.
